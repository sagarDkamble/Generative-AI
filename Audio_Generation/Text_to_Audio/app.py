import streamlit as st
import openai
from pathlib import Path

# Set page title
st.set_page_config(page_title="Text to Speech App", page_icon="🎙️")

st.title("🎙️ Text to Speech Generator")
st.write("Enter text and generate speech using OpenAI TTS.")

# Input for API key (for safety, users can enter their own key)
openai_api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

# Input for text
text_input = st.text_area("📝 Enter text to convert to speech:", 
                          "The quick brown fox jumped over the lazy dog.")

# Voice selection
voice = st.selectbox("🎤 Choose a voice:", ["alloy", "verse", "shimmer"])

# Button to generate
if st.button("Generate Speech"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key.")
    elif not text_input.strip():
        st.error("Please enter some text.")
    else:
        openai.api_key = openai_api_key

        # Define output file
        speech_file_path = Path("speech.mp3")

        # Generate speech
        with openai.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text_input
        ) as response:
            response.stream_to_file(speech_file_path)

        # Play audio in the app
        audio_file = open("speech.mp3", "rb")
        st.audio(audio_file.read(), format="audio/mp3")
        audio_file.close()

        st.success("✅ Speech generated successfully!")
