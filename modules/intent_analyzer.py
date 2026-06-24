import json
import logging
from google import genai
from google.genai import types

INTENT_PROMPT = """
Analyze the following outgoing SMS message being sent to {contact_name}.
Determine if the sender is making a firm commitment, confirming a scheduled event, or promising a specific action.

CRITICAL RULES FOR COMMITMENTS:
- "intent_level" MUST be "none" if there is no actionable intent or if it refers to past events.
- "intent_level" MUST be "maybe" if the sender is merely asking about availability, proposing a time, or confirming something without a concrete action item (e.g., "Would you be available?", "Does 2 PM work?", "The installer will take care of it").
- "intent_level" MUST be "firm" ONLY if the sender uses firm, declarative language explicitly promising an action or scheduling an event themselves (e.g., "I will be there at 2 PM", "I have scheduled the repair for Monday", "I promise to fix this tomorrow").

If it is an event/meeting, classify it as "event" (this is the default).
If it is a general promise without a specific date/time, classify it as "task".
If the sender says something like "in a couple of days", calculate the approximate future time or classify it as a task. 
(Assume current time is {current_time} in {timezone})

IMPORTANT: Write the summary from the sender's own perspective (first-person or imperative form). For example, use "Call {contact_name}" instead of "Sender will call {contact_name}".

Respond ONLY with a JSON object in this format:
{{
  "intent_level": "firm" | "maybe" | "none",
  "type": "event" | "task" | null,
  "summary": "Short description of the task/event including {contact_name}'s name (written from the user's POV)",
  "start_time": "YYYY-MM-DDTHH:MM:SS" (or null if it's just a task),
  "due_date": "YYYY-MM-DDTHH:MM:SS" (or null if it's just a task with no deadline)
}}

Message to analyze:
"{message}"
"""

CHAT_INTENT_PROMPT = """
Analyze the following recent SMS conversation with {contact_name}.
Your goal is to find the MOST RECENT un-actioned commitment or promise made by the sender ("Me").
Do not extract commitments made by {contact_name}. Only extract commitments made by "Me".

CRITICAL RULES FOR COMMITMENTS:
- "intent_level" MUST be "none" if there are no pending actionable commitments.
- "intent_level" MUST be "maybe" if "Me" is asking about availability, proposing a time, or mentioning a third party doing the work (e.g., "The installer will go").
- "intent_level" MUST be "firm" ONLY if "Me" explicitly promised an action or confirmed an event.

(Assume current time is {current_time} in {timezone})

Respond ONLY with a JSON object in this format:
{{
  "intent_level": "firm" | "maybe" | "none",
  "type": "event" | "task" | null,
  "summary": "Short description of the task/event including {contact_name}'s name (written from the user's POV)",
  "start_time": "YYYY-MM-DDTHH:MM:SS" (or null if it's just a task),
  "due_date": "YYYY-MM-DDTHH:MM:SS" (or null if it's just a task with no deadline)
}}

Conversation history:
{chat_history}
"""

def analyze_sms_intent(api_key: str, message: str, contact_name: str = "the contact", model: str = "gemini-2.5-flash", timezone: str = "Local") -> dict:
    """Uses Gemini to extract calendar/task intent from an SMS message."""
    if not api_key:
        logging.error("No Gemini API key provided for intent analysis.")
        return {"intent_level": "none"}
        
    try:
        client = genai.Client(api_key=api_key)
        import datetime
        current_time = datetime.datetime.now().isoformat()
        
        prompt = INTENT_PROMPT.format(current_time=current_time, message=message, contact_name=contact_name, timezone=timezone)
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        try:
            text = response.text
            if not text:
                return {"intent_level": "none"}
            result = json.loads(text)
            if result.get("intent_level") in ("firm", "maybe") and not result.get("type"):
                result["type"] = "event"
            return result
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from intent analyzer: {response.text}")
            return {"intent_level": "none"}
            
    except Exception as e:
        logging.error(f"Error communicating with Gemini for intent analysis: {e}")
        return {"intent_level": "none"}

def analyze_chat_history_intent(api_key: str, chat_history: str, contact_name: str = "the contact", model: str = "gemini-2.5-flash", timezone: str = "Local") -> dict:
    """Uses Gemini to find un-actioned commitments in recent chat history."""
    if not api_key:
        logging.error("No Gemini API key provided for chat intent analysis.")
        return {"intent_level": "none"}
        
    try:
        client = genai.Client(api_key=api_key)
        import datetime
        current_time = datetime.datetime.now().isoformat()
        
        prompt = CHAT_INTENT_PROMPT.format(current_time=current_time, chat_history=chat_history, contact_name=contact_name, timezone=timezone)
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        try:
            text = response.text
            if not text:
                return {"intent_level": "none"}
            result = json.loads(text)
            if result.get("intent_level") in ("firm", "maybe") and not result.get("type"):
                result["type"] = "event"
            return result
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from chat intent analyzer: {response.text}")
            return {"intent_level": "none"}
            
    except Exception as e:
        logging.error(f"Error communicating with Gemini for chat intent analysis: {e}")
        return {"intent_level": "none"}
