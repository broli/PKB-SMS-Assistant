import json
from modules.goto_api import GoToAPI
from modules.config_manager import load_config

api = GoToAPI()
url = f"{api.base_url}/messages"
config = load_config()
owner_number = config.get("goto_phone")

params = {
    "ownerPhoneNumber": api._clean_phone(owner_number),
    "contactPhoneNumber": "9097826041",
    "limit": 100
}

all_items = []
while True:
    resp = api._make_request("GET", url, params=params)
    data = resp.json()
    items = data.get("items", [])
    all_items.extend(items)
    marker = data.get("nextPageMarker")
    if not marker:
        break
    params["pageMarker"] = marker

# format the items
all_items = sorted(all_items, key=lambda x: x.get("timestamp", "") or x.get("createdAt", ""))

out = "# Full Conversation History: 909-782-6041\n\n"
for msg in all_items:
    direction = msg.get("direction", "").upper()
    author = msg.get("authorPhoneNumber", "")
    
    is_user = False
    if direction == "OUT":
        is_user = True
    elif direction == "IN":
        is_user = False
    elif author and api._phones_match(author, owner_number):
        is_user = True
        
    sender = "You" if is_user else "Contact"
    body = msg.get("body", "")
    time = msg.get("timestamp", "") or msg.get("createdAt", "")
    out += f"[{time}] **{sender}**: {body}\n"

with open("scratch/conversation_formatted_full.md", "w", encoding="utf-8") as f:
    f.write(out)
