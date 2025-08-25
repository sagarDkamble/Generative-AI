import gradio as gr
import base64
from openai import OpenAI
client = OpenAI()

def generate_image(prompt):
    try:
        img = client.images.generate(
            model="gpt-image-1",  # Make sure your organization is verified for this model
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_bytes = base64.b64decode(img.data[0].b64_json)
        # Save the image temporarily to display in Gradio
        with open("temp_output.png", "wb") as f:
            f.write(image_bytes)
        return "temp_output.png"
    except Exception as e:
        return f"Error generating image: {e}"

iface = gr.Interface(
    fn=generate_image,
    inputs=gr.Textbox(label="Enter prompt for image generation"),
    outputs=gr.Image(label="Generated Image"),
    title="OpenAI Image Generator"
)

iface.launch()
