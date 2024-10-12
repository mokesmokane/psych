import os
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from config import Config
from utils import process_image_with_ai, combine_images
import stripe
import logging
import threading
from flask_socketio import SocketIO
from PIL import Image
import io

# Global variable to store processed images temporarily
processed_images = []

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if Stability AI API key is set
if not os.environ.get('STABILITY_API_KEY'):
    raise ValueError("Stability AI API key is not set in the environment variables")

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

with app.app_context():
    import models
    db.create_all()

@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user = models.User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))

        new_user = models.User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = models.User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = models.User.query.get(session['user_id'])
    images = models.ProcessedImage.query.filter_by(user_id=user.id).all()

    return render_template('dashboard.html', user=user, images=images)

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        # Join a room named after the user_id
        socketio.emit('joined', {'room': session['user_id']})

def process_images_in_background(initial_image, iterations, user_id):
    with app.app_context():
        processed_image = initial_image
        processed_images = []

        # Emit the initial image to the client
        for i in range(iterations):
            logger.info(f'Processing image {i+1}/{iterations}')
            processed_image = process_image_with_ai(processed_image, iteration=i)
            if processed_image is None:
                logger.error(f'Failed to process image {i+1} with AI')
                break

            # Emit the processed image to the client
            encoded_image = base64.b64encode(processed_image).decode('utf-8')
            iteration = i + 1 if i != 4 else i + 2
            if i == 4:
                img = Image.open(io.BytesIO(initial_image)).convert('RGB')
                img = img.resize((1024, 1024))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                processed_images.append(img_byte_arr.getvalue())  # Append raw bytes
                encoded_initial_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                socketio.emit('image_processed', {'image_data': encoded_initial_image, 'iteration': 5})
            processed_images.append(processed_image)
            socketio.emit('image_processed', {'image_data': encoded_image, 'iteration': iteration})
            logger.info(f'Emitted processed image {i+1}/{iterations}')

        combined_image = combine_images(processed_images)  # Combine all processed images
        if combined_image is None:
            logger.error('Combined image is None, cannot proceed with encoding and saving.')
            return  # Exit the function or handle the error as needed

        user = models.User.query.get(user_id)
        new_image = models.ProcessedImage(user_id=user.id, image_data=combined_image)
        # Emit the combined image to the client
        encoded_image = base64.b64encode(combined_image).decode('utf-8')
        socketio.emit('final_image_processed', {'image_data': encoded_image})
        db.session.add(new_image)
        db.session.commit()
        logger.info(f'Saved combined image to database for user {user_id}')

@app.route('/process_image', methods=['GET', 'POST'])
def process_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'photo' not in request.files:
            logger.error('No file part in the request')
            return jsonify({'success': False, 'error': 'No file part in the request. Please select an image to upload.'})

        file = request.files['photo']
        iterations = int(request.form.get('iterations', 9))
        iterations = max(1, min(iterations, 9))  # Ensure iterations is between 1 and 9

        if file.filename == '':
            logger.error('No selected file')
            return jsonify({'success': False, 'error': 'No file selected. Please choose an image to upload.'})

        try:
            processed_image = file.read()  # Read the file data into memory

            # Start a background thread to process images
            thread = threading.Thread(target=process_images_in_background, args=(processed_image, iterations, session['user_id']))
            thread.start()

            return jsonify({'success': True, 'message': 'Image processing started', 'iterations': iterations})
        except Exception as e:
            logger.error(f'Error starting image processing: {str(e)}')
            return jsonify({'success': False, 'error': 'An error occurred while starting image processing.'})

    return render_template('process_image.html')

@app.route('/get_processed_images', methods=['GET'])
def get_processed_images():
    global processed_images
    return jsonify({'images': [base64.b64encode(img).decode('utf-8') for img in processed_images]})

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 1000,
                        'product_data': {
                            'name': 'Image Processing',
                            'description': 'AI-generated psychedelic effects',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=url_for('dashboard', _external=True),
            cancel_url=url_for('index', _external=True),
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        logger.error(f'Error creating checkout session: {str(e)}')
        return jsonify({'error': str(e)}), 403

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
