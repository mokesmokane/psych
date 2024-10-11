import os
import io
from PIL import Image
from openai import OpenAI
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def process_image_with_ai(image_file):
    try:
        logger.info('Opening and resizing input image')
        img = Image.open(image_file)
        img = img.resize((1024, 1024))  # DALL-E 2 requires 1024x1024 images
        
        logger.info('Converting image to bytes')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        logger.info('Calling OpenAI API to generate psychedelic version')
        response = client.images.create_variation(
            image=img_byte_arr,
            n=1,
            size="1024x1024"
        )

        logger.info('Getting URL of the generated image')
        image_url = response.data[0].url

        logger.info('Downloading the generated image')
        generated_image = requests.get(image_url).content

        return generated_image

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

def combine_images(images):
    try:
        logger.info('Combining processed images into a 3x3 grid')
        base_img = Image.open(io.BytesIO(images[0]))
        width, height = base_img.size
        new_img = Image.new('RGB', (width * 3, height * 3))
        
        for i, img_bytes in enumerate(images):
            img = Image.open(io.BytesIO(img_bytes))
            x = (i % 3) * width
            y = (i // 3) * height
            new_img.paste(img, (x, y))
        
        logger.info('Converting combined image to bytes')
        img_byte_arr = io.BytesIO()
        new_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
    except Exception as e:
        logger.error(f"Error combining images: {str(e)}")
        return None
