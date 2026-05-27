import json
import os

CONTACTS_FILE = "contacts.json"


def load_contacts() -> dict:
    """Load contacts from local cache. Returns { phone: {name, nickname} }."""
    if not os.path.exists(CONTACTS_FILE):
        return {}
    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Normalise: migrate old plain-string format { phone: "Name" } if needed
        normalised = {}
        for phone, value in data.items():
            if isinstance(value, str):
                normalised[phone] = {"name": value, "nickname": ""}
            else:
                normalised[phone] = {
                    "name":     value.get("name", ""),
                    "nickname": value.get("nickname", ""),
                }
        return normalised
    except Exception as e:
        print(f"[contact_book] Error loading contacts: {e}")
        return {}


def save_contacts(contacts_dict: dict) -> bool:
    """Persist contacts dict to disk."""
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts_dict, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[contact_book] Error saving contacts: {e}")
        return False


def get_display_name(phone: str, contacts_dict: dict) -> str:
    """
    Returns the best available display label for a phone number.
    Priority: nickname > GoTo name > phone number (fallback).
    """
    entry = contacts_dict.get(phone)
    if not entry:
        return phone
    nickname = entry.get("nickname", "").strip()
    if nickname:
        return nickname
    name = entry.get("name", "").strip()
    if name:
        return name
    return phone


def set_nickname(phone: str, nickname: str, contacts_dict: dict) -> dict:
    """
    Set or update the local nickname for a phone number.
    Creates an entry if it doesn't exist. Saves to disk.
    Returns the updated contacts_dict.
    """
    if phone not in contacts_dict:
        contacts_dict[phone] = {"name": "", "nickname": nickname.strip()}
    else:
        contacts_dict[phone]["nickname"] = nickname.strip()
    save_contacts(contacts_dict)
    return contacts_dict


def _clean_phone(raw_phone: str) -> str:
    """Internal helper to normalise phone to E.164."""
    digits = "".join(c for c in str(raw_phone) if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) >= 11:
        return f"+{digits}"
    return ""


def analyze_raw_text(file_path: str) -> dict:
    """
    Parses GoTo copy-pasted text and computes a delta against current contacts.
    Returns: {
        "new":      {phone: name},      # not in db
        "update":   {phone: {old: str, new: str}}, # in db but no nickname
        "preserve": {phone: {name: str, nick: str}}, # in db with nickname (skipped)
        "total_scanned": int
    }
    """
    current_db = load_contacts()
    
    plan = {
        "new": {},
        "update": {},
        "preserve": {},
        "total_scanned": 0
    }

    if not os.path.exists(file_path):
        return plan

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        plan["total_scanned"] = len(lines)

        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
                
            name = lines[i]
            type_str = lines[i+1]
            phone_raw = lines[i+2]
            
            # Basic validation just in case
            if type_str.lower() not in ("private", "shared", "company"):
                continue
                
            # Skip header noise if accidentally present
            if name in ("Name", "Type", "Phone number", "Email address", "--"):
                continue
                
            if phone_raw == "--" or "@" in phone_raw:
                continue
                
            phone = _clean_phone(phone_raw)
            if not phone:
                continue
                
            if phone in current_db:
                entry = current_db[phone]
                if entry.get("nickname"):
                    plan["preserve"][phone] = {
                        "name": entry.get("name", ""),
                        "nick": entry.get("nickname")
                    }
                else:
                    old_name = entry.get("name", "")
                    if old_name != name:
                        plan["update"][phone] = {"old": old_name, "new": name}
                    else:
                        # Name is exactly the same, count as preserve/no-change
                        plan["preserve"][phone] = {"name": name, "nick": ""}
            else:
                plan["new"][phone] = name

    except Exception as e:
        print(f"[contact_book] Error analyzing text: {e}")

    return plan


def apply_import_plan(plan: dict) -> bool:
    """Updates contacts.json based on the computed plan."""
    db = load_contacts()
    
    # Add new ones
    for phone, name in plan.get("new", {}).items():
        db[phone] = {"name": name, "nickname": ""}
        
    # Update existing (those without nicknames)
    for phone, data in plan.get("update", {}).items():
        if phone in db:
            db[phone]["name"] = data["new"]
            
    return save_contacts(db)
