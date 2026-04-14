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

def generate_reply(api_key, chat_history, tone, intent, receiver_name="Receiver", custom_prompt=None):
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
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {e}"
