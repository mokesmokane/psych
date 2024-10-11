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

def process_image_with_ai(image_file, iteration=0):
    try:
        logger.info(f'Processing image iteration {iteration + 1}')
        img = Image.open(image_file)
        img = img.resize((1024, 1024))  # DALL-E 2 requires 1024x1024 images
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Increase intensity of psychedelic effects with each iteration
        intensity = min(iteration * 0.2 + 0.2, 1.0)  # Scale from 0.2 to 1.0
        prompt = f"Transform this image into a vibrant, colorful, and surreal psychedelic artwork. Intensity: {intensity:.1f}"
        
        logger.info(f'Calling OpenAI API with prompt: {prompt}')
        try:
            response = client.images.create_variation(
                image=img_byte_arr,
                n=1,
                size="1024x1024",
                prompt=prompt
            )
        except Exception as api_error:
            logger.error(f"Error calling OpenAI API: {str(api_error)}")
            raise ValueError("Failed to generate image variation using OpenAI API")

        image_url = response.data[0].url
        if not image_url:
            raise ValueError("OpenAI API response does not contain an image URL")

        logger.info('Downloading the generated image')
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            generated_image = response.content
        except requests.RequestException as req_error:
            logger.error(f"Error downloading generated image: {str(req_error)}")
            raise ValueError("Failed to download the generated image")

        return generated_image

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

def combine_images(images):
    try:
        logger.info('Combining processed images into a 3x3 grid')
        if len(images) != 9:
            raise ValueError(f"Expected 9 images, but got {len(images)}")

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
