from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import os
from uuid import uuid4

import glob
import time

from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/instagram_images", StaticFiles(directory="instagram_images"), name="instagram_images")

# Define the path to save the images
SAVE_PATH = "instagram_images"
os.makedirs(SAVE_PATH, exist_ok=True)

# Define a Pydantic model for the request body
class ImageRequest(BaseModel):
    image_url: str
    banner_text: str
    description_text: str
    footer_text: str


def manage_image_storage(save_path, max_images=5):

    # Get a list of all images in the folder sorted by modification time
    images = sorted(glob.glob(os.path.join(save_path, "*.jpg")), key=os.path.getmtime)
    
    # Delete oldest images if more than max_images exist
    while len(images) > max_images:
        oldest_image = images.pop(0)
        os.remove(oldest_image)

@app.post("/create_instagram_image/")
async def create_instagram_image(request: ImageRequest):
    try:
        # Download the image
        response = requests.get(request.image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the image.")
        original_img = Image.open(BytesIO(response.content))

        # Define the sizes for the new image
        img_size = 1080
        banner_height = 120
        desc_height = 250  # Increase height to account for wrapped text
        footer_height = 180

        # Calculate total height for new image (image + banner + description + footer)
        total_height = img_size + banner_height + desc_height + footer_height

        # Create a new image with space for banner and text below
        new_img = Image.new('RGB', (img_size, total_height), color='white')

        # Resize and paste the original image into the center of the new image
        original_img = original_img.resize((img_size, img_size), Image.LANCZOS)
        x_offset = 0
        y_offset = banner_height  # start after the banner space
        new_img.paste(original_img, (x_offset, y_offset))

        draw = ImageDraw.Draw(new_img)

        # Load fonts
        banner_font = ImageFont.truetype("font/Oswald-Bold.ttf", 60)
        desc_font = ImageFont.truetype("font/Oswald-Bold.ttf", 40)
        footer_font = ImageFont.truetype("font/Oswald-Bold.ttf", 36)

        # Define background colors
        banner_bg_color = '#FFD700'  # Gold
        desc_bg_color = '#ADD8E6'    # Light Blue
        footer_bg_color = '#90EE90'  # Light Green

        # Draw background rectangles for each section
        draw.rectangle([0, 0, img_size, banner_height], fill=banner_bg_color)
        draw.rectangle([0, img_size + banner_height, img_size, img_size + banner_height + desc_height + 90], fill=desc_bg_color)
        draw.rectangle([0, total_height - footer_height + (footer_height - 40) / 2, img_size, total_height], fill=footer_bg_color)

        # Add banner text at the top
        banner_text_width, banner_text_height = draw.textbbox((0, 0), request.banner_text, font=banner_font)[2:]
        draw.text(((img_size - banner_text_width) / 2, (banner_height - banner_text_height) / 2), 
                  request.banner_text, font=banner_font, fill='black', align='center')

        # Wrap the description text to fit within the available width
        max_desc_width = img_size - 40  # margin of 20px on each side
        wrapped_desc_text = textwrap.fill(request.description_text, width=60)  # Adjust width as necessary

        # Add description text below the image
        draw.multiline_text(((img_size - max_desc_width + 70) / 2, img_size + banner_height), 
                            wrapped_desc_text, font=desc_font, fill='black', align='center')

        # Add footer text at the very bottom
        footer_text_width, footer_text_height = draw.textbbox((0, 0), request.footer_text, font=footer_font)[2:]
        draw.text(((img_size - footer_text_width) / 2, total_height - footer_height + (footer_height - footer_text_height + 60) / 2), 
                  request.footer_text, font=footer_font, fill='black', align='center')
        
        # Save the image in the specified folder
        image_id = str(uuid4())
        image_filename = f"{SAVE_PATH}/{image_id}.jpg"
        new_img.save(image_filename, quality=95)

        # Manage image storage (ensure max 30 images in the folder)
        manage_image_storage(SAVE_PATH, max_images=5)

        # Construct the URL for the saved image
        # image_url = f"http://localhost:8000/instagram_images/{image_id}.jpg"
        image_url = f"https://socialautomation.onrender.com/instagram_images/{image_id}.jpg"

        return {"message": "Image created successfully", "image_url": image_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Usage
# url = "https://i.ibb.co/8XtqXRq/Screenshot-2024-08-16-at-1-31-10-AM.png"
# banner = "Hindenburg's systematic attack"
# description = "RBI, SEBI are amongst the finest in the world. Do not overreact and let facts come out. This is not in isolation! Gurmeet Chadha, Managing Partner & CIO of Complete Circle Capital argued that the allegations were part of a systematic attack on Indian institutions Capital argued that the allegations were part of a "
# footer = "WaveFlash Latest"

# result = create_instagram_image(url, banner, description, footer)
# result.save("instagram_image.jpg", quality=95)


# 45-50 words for desc
# 1-3 words for banner