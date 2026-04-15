from modules.config_manager import load_config
import requests

config = load_config()
token = config.get("access_token")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

print("=== Probing voice-admin/v1/contacts ===\n")

resp = requests.get("https://api.goto.com/voice-admin/v1/contacts", headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Response (first 1000):\n{resp.text[:1000]}")
