import streamlit as st
from openai import OpenAI
import base64

client = OpenAI()

st.title("AI-Powered Dermatology Assistant 🧑‍⚕️")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    if st.button("Analyze"):
        with st.spinner("Analyzing image... ⏳"):
            # Convert to base64
            file_bytes = uploaded_file.read()
            base64_image = base64.b64encode(file_bytes).decode("utf-8")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a dermatologist assistant. Analyze the image and suggest possible conditions (not a medical diagnosis)."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please analyze this image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            st.success(response.choices[0].message["content"])
