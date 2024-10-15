import gradio as gr
import io
from PIL import Image
from utils import process_image_with_ai
import base64
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now you can access the environment variables like this:
STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')

def process_image(input_image, prompt, num_iterations):
    input_image_bytes = io.BytesIO()
    input_image.save(input_image_bytes, format='PNG')
    input_image_bytes = input_image_bytes.getvalue()
    
    processed_images = []
    for i in range(num_iterations):
        processed_image = process_image_with_ai(input_image_bytes, prompt, i)
        if processed_image:
            pil_image = Image.open(io.BytesIO(processed_image))
            processed_images.append(pil_image)
    
    return processed_images

examples = [
    ["path/to/example/image1.jpg", "A vibrant, colorful, floral and surreal psychedelic artwork", 3],
    ["path/to/example/image2.jpg", "A neon-lit cyberpunk cityscape with flying cars", 3],
    ["path/to/example/image3.jpg", "An ethereal underwater scene with bioluminescent creatures", 3],
]

iface = gr.Interface(
    fn=process_image,
    inputs=[
        gr.Image(type="pil", label="Input Image"),
        gr.Textbox(label="Prompt", value="A vibrant, colorful, floral and surreal psychedelic artwork"),
        gr.Slider(minimum=1, maximum=9, step=1, value=3, label="Number of Iterations")
    ],
    outputs=[gr.Gallery(label="Processed Images", columns=3, rows=3)],
    title="Psychedelic Image Processor",
    description="Upload an image and apply AI-generated psychedelic effects!",
    examples=examples
)

if __name__ == "__main__":
    iface.launch()
