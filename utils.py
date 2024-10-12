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
        logger.info('Starting outpainting process')
        img = Image.open(image_file).convert('RGBA')
        img = img.resize((1024, 1024))  # DALL-E 3 requires 1024x1024 images
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        for i in range(3):
            logger.info(f'Outpainting iteration {i+1}')
            prompt = f"Expand this image outwards, creating a larger scene that complements the original content. Iteration {i+1}/3"
            
            try:
                response = client.images.edit(
                    image=img_byte_arr,
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )
            except Exception as api_error:
                logger.error(f"Error calling OpenAI API: {str(api_error)}")
                raise ValueError("Failed to generate outpainted image using OpenAI API")

            image_url = response.data[0].url
            if not image_url:
                raise ValueError("OpenAI API response does not contain an image URL")

            logger.info('Downloading the generated image')
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                img_byte_arr = io.BytesIO(response.content)
            except requests.RequestException as req_error:
                logger.error(f"Error downloading generated image: {str(req_error)}")
                raise ValueError("Failed to download the generated image")

        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

# Remove the combine_images function as it's no longer needed
