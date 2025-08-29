import streamlit as st
from openai import OpenAI

client = OpenAI()

st.title("AI-Powered Dermatology Assistant 🧑‍⚕️")

uploaded_file = st.file_uploader("Upload an image of the skin condition", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    if st.button("Analyze"):
        with st.spinner("Analyzing image... ⏳"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # or gpt-4o if available
                messages=[
                    {"role": "system", "content": "You are a dermatologist assistant. You can analyze skin images and suggest possible conditions (not a medical diagnosis)."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Please analyze this image and suggest possible conditions."},
                        {"type": "image_url", "image_url": {"url": uploaded_file.name}}
                    ]}
                ]
            )
            st.success(response.choices[0].message["content"])
