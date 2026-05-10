import json
import os
import base64
import threading

CONFIG_FILE = "config.dat"
CONFIG_LOCK = threading.Lock()
_RUNTIME_OVERRIDES = {}

def set_runtime_override(key, value):
    """Sets a config value in memory only. It will not be saved to disk."""
    with CONFIG_LOCK:
        _RUNTIME_OVERRIDES[key] = value

def scramble(data_str):
    # Weak layer of encryption: reverse string and base64 encode
    return base64.b64encode(data_str[::-1].encode()).decode()
    
def unscramble(scrambled_str):
    try:
        decoded_bytes = base64.b64decode(scrambled_str.encode()).decode()
        return decoded_bytes[::-1]
    except Exception:
        return "{}"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "access_token": "",
            "refresh_token": "",
            "goto_phone": "",
            "gemini_api_key": "",
            "gemini_api_key_paid": "", # [NEW]
            "custom_prompt": ""
        }

    with CONFIG_LOCK:
        try:
            with open(CONFIG_FILE, "r") as f:
                scrambled = f.read()
                json_str = unscramble(scrambled)
                config = json.loads(json_str)
                # Merge runtime overrides
                config.update(_RUNTIME_OVERRIDES)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "access_token": "",
                "refresh_token": "",
                "goto_phone": "",
                "gemini_api_key": "",
                "gemini_api_key_paid": "", # [NEW]
                "custom_prompt": ""
            }


def save_config(config_data):
    with CONFIG_LOCK:
        try:
            # Create a copy to save so we don't save runtime overrides
            save_data = config_data.copy()
            for key in _RUNTIME_OVERRIDES:
                save_data.pop(key, None)
                
            json_str = json.dumps(save_data)
            scrambled = scramble(json_str)
            with open(CONFIG_FILE, "w") as f:
                f.write(scrambled)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
