import os
import io
from PIL import Image
import openai
from openai import OpenAIError
import requests

# Set up the OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

def process_image_with_ai(image_file):
    try:
        # Open and resize the input image
        img = Image.open(image_file)
        img = img.resize((1024, 1024))  # DALL-E 2 requires 1024x1024 images
        
        # Convert the image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Use DALL-E 2 to generate a psychedelic version of the image
        response = openai.Image.create_variation(
            image=img_byte_arr,
            n=1,
            size="1024x1024"
        )

        # Get the URL of the generated image
        image_url = response.data[0].url

        # Download the generated image
        generated_image = requests.get(image_url).content

        return generated_image

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

def combine_images(images):
    # Combine the 9 processed images into a single image
    # For simplicity, we'll create a 3x3 grid of the processed images
    base_img = Image.open(io.BytesIO(images[0]))
    width, height = base_img.size
    new_img = Image.new('RGB', (width * 3, height * 3))
    
    for i, img_bytes in enumerate(images):
        img = Image.open(io.BytesIO(img_bytes))
        x = (i % 3) * width
        y = (i // 3) * height
        new_img.paste(img, (x, y))
    
    # Convert the combined image to bytes
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr
