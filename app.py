import os
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from config import Config
from utils import process_image_with_ai, combine_images
import stripe

# Check if OpenAI API key is set
if not os.environ.get('OPENAI_API_KEY'):
    raise ValueError("OpenAI API key is not set in the environment variables")

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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

@app.route('/process_image', methods=['GET', 'POST'])
def process_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            try:
                processed_images = []
                for _ in range(9):
                    processed_image = process_image_with_ai(file)
                    if processed_image is None:
                        raise ValueError("Failed to process image with AI")
                    processed_images.append(processed_image)
                
                final_image = combine_images(processed_images)
                
                user = models.User.query.get(session['user_id'])
                new_image = models.ProcessedImage(user_id=user.id, image_data=final_image)
                db.session.add(new_image)
                db.session.commit()
                
                flash('Image processed successfully')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Error processing image: {str(e)}')
                return redirect(request.url)
    
    return render_template('process_image.html')

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
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
