import os
import openai
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = "You are a helpful AI assistant. Keep answers concise and clear."

def get_gpt_response(prompt, history=None, model="gpt-4o-mini", temperature=0.7):
    if history is None:
        history = []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return resp["choices"][0]["message"]["content"]
