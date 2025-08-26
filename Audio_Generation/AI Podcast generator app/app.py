import streamlit as st
import openai
from pathlib import Path

# Page setup
st.set_page_config(page_title="Podcast Generator", page_icon="🎧")

st.title("🎧 AI Podcast Generator")
st.write("Generate a podcast script and audio based on a topic using OpenAI.")

# Input for API key
openai_api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

# Input for podcast topic
topic = st.text_input("📝 Enter a podcast topic:", "The Future of Artificial Intelligence")

# Button to generate
if st.button("Generate Podcast"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key.")
    elif not topic.strip():
        st.error("Please enter a podcast topic.")
    else:
        openai.api_key = openai_api_key

        with st.spinner("🎬 Generating podcast script..."):
            # Step 1: Generate podcast script
            script_response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Lighter model, faster for generation
                messages=[
                    {"role": "system", "content": "You are a podcast script writer."},
                    {"role": "user", "content": f"Write a detailed, engaging podcast script about {topic}. Make it around 500 words."}
                ]
            )
            podcast_script = script_response.choices[0].message.content

        st.subheader("📜 Generated Podcast Script")
        st.write(podcast_script)

        with st.spinner("🎙️ Converting script to speech..."):
            # Step 2: Convert script to audio
            speech_file_path = Path("podcast.mp3")

            with openai.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=podcast_script
            ) as response:
                response.stream_to_file(speech_file_path)

        # Step 3: Play podcast
        audio_file = open("podcast.mp3", "rb")
        st.audio(audio_file.read(), format="audio/mp3")
        audio_file.close()

        st.success("✅ Podcast generated successfully!")
