import os
import time
import logging
import streamlit as st
from rembg import remove
from PIL import Image
from werkzeug.utils import secure_filename
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webp'])
MAX_FILE_SIZE = 10 * 1024 * 1024  # Max file size: 10MB

# Make sure the necessary directories exist
if 'static' not in os.listdir('.'):
    os.mkdir('static')

if 'uploads' not in os.listdir('static/'):
    os.mkdir('static/uploads')

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to check file size
def check_file_size(file):
    if len(file.getbuffer()) > MAX_FILE_SIZE:
        st.error("File is too large. Please upload a smaller file.")
        return False
    return True

# Function to remove the background of the image
@st.cache_data  # Use caching for faster performance (for data processing)
def remove_background(input_path, output_path):
    input = Image.open(input_path)
    output = remove(input)
    output.save(output_path)
    return output_path

# Function to replace background color
def replace_background_color(input_path, output_path, color=(255, 255, 255)):
    image = Image.open(input_path)
    image = image.convert("RGBA")
    datas = image.getdata()

    new_data = []
    for item in datas:
        # Change all transparent pixels to the specified color
        if item[3] == 0:
            new_data.append(color + (255,))
        else:
            new_data.append(item)
    
    image.putdata(new_data)
    image.save(output_path)
    return output_path

# Streamlit app
def main():
    # Page Title
    st.title('Background Remover with Streamlit')

    # File upload section for multiple images
    uploaded_files = st.file_uploader("Choose images", type=ALLOWED_EXTENSIONS, accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.image(uploaded_file, caption=f"Original Image: {uploaded_file.name}", use_container_width=True)

            # Check file size
            if not check_file_size(uploaded_file):
                continue
            
            # File handling
            filename = secure_filename(uploaded_file.name)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Resizing options
            resize_width = st.slider(f"Resize Width for {filename}", min_value=100, max_value=1000, value=500)
            resize_height = st.slider(f"Resize Height for {filename}", min_value=100, max_value=1000, value=500)

            image = Image.open(uploaded_file)
            image_resized = image.resize((resize_width, resize_height))
            st.image(image_resized, caption=f"Resized Image: {filename}", use_container_width=True)

            # Rotate and crop options
            rotation_angle = st.slider("Rotate the image", min_value=0, max_value=360, value=0)
            image_resized = image_resized.rotate(rotation_angle)
            st.image(image_resized, caption="Rotated Image", use_container_width=True)

            crop = st.checkbox("Crop Image")
            if crop:
                left = st.slider("Left", 0, image_resized.width, 0)
                upper = st.slider("Upper", 0, image_resized.height, 0)
                right = st.slider("Right", 0, image_resized.width, image_resized.width)
                lower = st.slider("Lower", 0, image_resized.height, image_resized.height)
                image_resized = image_resized.crop((left, upper, right, lower))
                st.image(image_resized, caption="Cropped Image", use_container_width=True)

            # Background removal model selection
            model_choice = st.selectbox(f"Choose Background Removal Model for {filename}", 
                                        ["Default Model", "Custom Model 1", "Custom Model 2"])

            # Background color replacement option
            bg_color = st.color_picker("Pick a background color", "#FFFFFF")

            if st.button(f"Remove Background for {filename}"):
                # Show progress bar
                progress = st.progress(0)

                rembg_img_name = filename.split('.')[0] + "_rembg.png"
                rembg_img_path = os.path.join(UPLOAD_FOLDER, rembg_img_name)

                # Save the resized and edited image and remove the background
                temp_resized_path = os.path.join(UPLOAD_FOLDER, "temp_resized.png")
                image_resized.save(temp_resized_path)
                st.progress(50)  # Update progress bar

                # Process background removal
                final_img_path = remove_background(temp_resized_path, rembg_img_path)
                st.progress(100)  # Update progress bar

                if bg_color != "#FFFFFF":  # Replace transparent background if color is selected
                    replace_background_color(final_img_path, rembg_img_path, color=tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5)))
                    st.image(rembg_img_path, caption=f"Processed Image with Color: {filename}", use_container_width=True)
                else:
                    st.image(rembg_img_path, caption=f"Processed Image: {filename}", use_container_width=True)

                # Provide a download button for each processed image
                with open(rembg_img_path, "rb") as file:
                    st.download_button(
                        label=f"Download Processed Image {filename}",
                        data=file,
                        file_name=rembg_img_name,
                        mime="image/png"
                    )

                # Log the event for analytics
                logging.info(f"Image processed and downloaded: {uploaded_file.name}")

    else:
        st.info("Please upload an image to get started.")

if __name__ == "__main__":
    main()
