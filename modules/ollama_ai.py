import requests
import json

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

DEFAULT_PROMPT = """
You are an expert communication assistant for a project manager.
Review the following SMS conversation and generate a single reply based on the requested tone and intent.

The messages are labeled:
- "Me" = the person sending this reply (you are writing on their behalf)
- "{receiver_name}" = the other person in the conversation

Chat History:
{chat_history}

Desired Tone: {tone}
Intent (What I want to convey): {intent}

Please provide ONLY the raw text of the message to send back to {receiver_name}. Be concise and natural for an SMS message. Do not include quotes around the message.
"""

def is_ollama_available():
    """Checks if Ollama is running on localhost."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def generate_reply(chat_history, tone, intent, receiver_name="Receiver", custom_prompt=None):
    """Uses local Ollama (llama3) to generate a response."""
    try:
        base_prompt = custom_prompt if custom_prompt else DEFAULT_PROMPT
        
        try:
            prompt = base_prompt.format(
                chat_history=chat_history,
                tone=tone,
                intent=intent,
                receiver_name=receiver_name
            )
        except KeyError as e:
            return f"Error in custom prompt: Missing placeholder {e}."

        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            return f"Error from Ollama: {response.status_code}"
            
    except Exception as e:
        return f"Error communicating with Ollama: {e}"
