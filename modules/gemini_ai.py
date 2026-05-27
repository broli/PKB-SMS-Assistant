from google import genai

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

def get_sorted_models(api_key):
    """Fetches available Gemini models, filters for content generation capability, and sorts them by heuristic score."""
    if not api_key:
        return []
    try:
        client = genai.Client(api_key=api_key)
        models_list = list(client.models.list())
        supported_names = []
        for m in models_list:
            name = m.name
            if "generateContent" not in (m.supported_actions or []): continue
            if name.startswith("models/"): name = name[7:]
            # Exclude old or vision-only models
            if name.startswith("gemini-1.0") or name == "gemini-pro" or "vision" in name:
                continue
            supported_names.append(name)
            
        def _score_model(m: str) -> int:
            score = 0
            if "gemini-3.1" in m: score += 1000
            elif "gemini-3.0" in m: score += 900
            elif "gemini-2.5" in m: score += 800
            elif "gemini-2.0" in m: score += 700
            elif "gemini-1.5" in m: score += 600
            if "pro" in m: score += 50
            if "exp" in m: score -= 5
            return score
            
        supported_names.sort(key=_score_model, reverse=True)
        return supported_names
    except Exception as e:
        print(f"Error fetching Gemini models: {e}")
        return []

def generate_reply(api_key, chat_history, tone, intent, receiver_name="Receiver", custom_prompt=None, model="gemini-2.5-flash"):
    """Uses Gemini to generate a response based on history, tone, and user intent."""
    if not api_key:
        return "Error: Gemini API key is missing. Please add it in Settings."
        
    try:
        client = genai.Client(api_key=api_key)
        
        base_prompt = custom_prompt if custom_prompt else DEFAULT_PROMPT
        
        try:
            prompt = base_prompt.format(
                chat_history=chat_history,
                tone=tone,
                intent=intent,
                receiver_name=receiver_name
            )
        except KeyError as e:
            return f"Error in custom prompt: Missing placeholder {e}. Use {{chat_history}}, {{tone}}, {{intent}}, and {{receiver_name}}."
            
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {e}"
