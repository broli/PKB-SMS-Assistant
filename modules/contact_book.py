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
