import json
import os
import time

HISTORY_FILE = "history.json"
AI_COOLDOWN_SECONDS = 1 * 60  # 1 minute
GOTO_COOLDOWN_SECONDS = 30     # 30 seconds

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"last_ai_call": 0, "last_goto_pull": 0}
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            # Ensure keys exist
            if "last_ai_call" not in data: data["last_ai_call"] = 0
            if "last_goto_pull" not in data: data["last_goto_pull"] = 0
            return data
    except Exception:
        return {"last_ai_call": 0, "last_goto_pull": 0}

def save_history(history_data):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_data, f, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")

def get_remaining_cooldown(key="last_ai_call", cooldown_seconds=AI_COOLDOWN_SECONDS):
    """Returns the remaining cooldown time in seconds for a specific key, or 0 if allowed."""
    history = load_history()
    last_call = history.get(key, 0)
    current_time = time.time()
    
    elapsed = current_time - last_call
    if elapsed >= cooldown_seconds:
        return 0
    return int(cooldown_seconds - elapsed)

def record_ai_call():
    """Update the history file with the current timestamp for AI calls."""
    history = load_history()
    history["last_ai_call"] = time.time()
    save_history(history)

def record_goto_call():
    """Update the history file with the current timestamp for GoTo calls."""
    history = load_history()
    history["last_goto_pull"] = time.time()
    save_history(history)
