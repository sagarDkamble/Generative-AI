import streamlit as st
from openai import OpenAI
import base64

client = OpenAI()

st.title("📘 AI Homework Helper")

uploaded_file = st.file_uploader("Upload a photo of your math problem", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Problem", width="stretch")

    if st.button("Solve"):
        with st.spinner("Analyzing and solving... ⏳"):
            # Convert image to base64
            file_bytes = uploaded_file.read()
            base64_image = base64.b64encode(file_bytes).decode("utf-8")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert math tutor. "
                            "Your task is to carefully analyze the math problem in the image. "
                            "Solve it step by step using clear explanations, equations, and reasoning. "
                            "Always format math properly using LaTeX (so it looks neat in the output). "
                            "Show formulas, intermediate steps, and the final answer in a structured way. "
                            "If multiple methods exist, explain the most efficient one. "
                            "Keep it simple, clear, and student-friendly."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please solve this math problem with detailed steps and proper formulas."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            )

            answer = response.choices[0].message.content
            st.markdown("### ✅ Solution")
            st.write(answer)
