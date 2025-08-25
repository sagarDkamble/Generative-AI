import streamlit as st
import base64
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Streamlit App
st.title("🖼️ OpenAI Image Generator")
st.write("Enter a prompt below to generate an image using OpenAI's model.")

# Input prompt
prompt = st.text_input("Enter prompt for image generation:")

if st.button("Generate Image"):
    if prompt:
        try:
            with st.spinner("Generating image... ⏳"):
                # Call OpenAI Image API
                img = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )

                # Decode base64 image
                image_bytes = base64.b64decode(img.data[0].b64_json)

                # Save temp image
                with open("generated_image.png", "wb") as f:
                    f.write(image_bytes)

                # Display in Streamlit
                st.image("generated_image.png", caption="Generated Image", use_column_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a prompt first!")
