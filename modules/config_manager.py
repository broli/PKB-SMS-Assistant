import json
import os
import base64

CONFIG_FILE = "config.dat"

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

    try:
        with open(CONFIG_FILE, "r") as f:
            scrambled = f.read()
            json_str = unscramble(scrambled)
            return json.loads(json_str)
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
    try:
        json_str = json.dumps(config_data)
        scrambled = scramble(json_str)
        with open(CONFIG_FILE, "w") as f:
            f.write(scrambled)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
