import os
import io
from PIL import Image
import requests
import logging
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the Stability AI API key
STABILITY_API_KEY = os.environ.get('STABILITY_API_KEY')
if not STABILITY_API_KEY:
    raise ValueError(
        "Stability AI API key is not set in the environment variables")


def process_image_with_ai(image_data, iteration=0):
    try:
        logger.info(f'Processing image iteration {iteration + 1}')
        img = Image.open(io.BytesIO(image_data)).convert('RGB')
        img = img.resize((1024, 1024))  # Stability AI requires 512x512 images

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        prompt = "A vibrant, colorful, floral and surreal psychedelic artwork"

        logger.info(f'Calling Stability AI API with prompt: {prompt}')
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {STABILITY_API_KEY}"
                },
                files={"init_image": img_byte_arr},
                data={
                    "init_image_mode": "IMAGE_STRENGTH",
                    "image_strength": 0.25,
                    "text_prompts[0][text]": prompt,
                    "text_prompts[0][weight]": 1.0,
                    "cfg_scale": 7,
                    "samples": 1,
                    "steps": 10,
                })
            if response.status_code != 200:
                logger.error(
                    f'Stability AI API call failed with status code {response.json()}'
                )
            response.raise_for_status()
        except requests.exceptions.RequestException as api_error:
            logger.error(f"Error calling Stability AI API: {str(api_error)}")
            raise ValueError("Failed to generate image using Stability AI API")

        if response.status_code != 200:
            raise ValueError(f"Non-200 response: {str(response.text)}")

        data = response.json()

        if "artifacts" not in data:
            raise ValueError(
                "Stability AI API response does not contain artifacts")

        image_data_base64 = data["artifacts"][0]["base64"]
        image_data = base64.b64decode(image_data_base64)

        return image_data

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
