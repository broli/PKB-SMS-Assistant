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

def get_best_model():
    """Queries Ollama for available models and returns the best llama3 match."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            # Prefer exact llama3 if it exists
            if "llama3:latest" in model_names or "llama3" in model_names:
                return "llama3"
            
            # Look for llama3.1 or others starting with llama3
            for name in model_names:
                if name.startswith("llama3.1"):
                    return name
                if "llama3" in name:
                    return name
                    
        return DEFAULT_MODEL # Fallback to llama3
    except Exception:
        return DEFAULT_MODEL

def generate_reply(chat_history, tone, intent, receiver_name="Receiver", custom_prompt=None):
    """Uses local Ollama to generate a response."""
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

        model = get_best_model()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            try:
                error_msg = response.json().get("error", "Unknown error")
                return f"Error from Ollama ({response.status_code}): {error_msg}"
            except:
                return f"Error from Ollama: {response.status_code}"
            
    except Exception as e:
        return f"Error communicating with Ollama: {e}"
