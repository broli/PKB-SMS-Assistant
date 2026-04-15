import csv
import json
import os
import re

CONTACTS_FILE = "contacts.json"

def clean_phone(raw_phone):
    """Keep only digits, prepend + for E.164 style mapping if needed."""
    if not raw_phone:
        return ""
    digits = "".join(c for c in raw_phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) > 10:
        return f"+{digits}"
    return raw_phone

def merge_csv_to_contacts(csv_path):
    print(f"Reading CSV: {csv_path}")
    
    # Load existing contacts if any
    existing_contacts = {}
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            try:
                existing_contacts = json.load(f)
            except json.JSONDecodeError:
                pass
                
    added_count = 0
    updated_count = 0
    
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        # We don't know if they exported Google CSV or Outlook CSV.
        # We will look for common phone column names.
        phone_columns = ["Phone", "Mobile Phone", "Business Phone", "Home Phone", "Primary Phone", "Phones"]
        
        for row in reader:
            # Common name columns
            first_name = row.get("First Name", "").strip()
            last_name = row.get("Last Name", "").strip()
            name = f"{first_name} {last_name}".strip()
            if not name:
                name = row.get("Name", "").strip()
                
            for col, val in row.items():
                if val and any(p_col.lower() in (col.lower() if col else "") for p_col in phone_columns):
                    phone = clean_phone(val)
                    if not phone: continue
                    
                    if phone in existing_contacts:
                        # Only update if existing has no name or nickname
                        if not existing_contacts[phone].get("name") and not existing_contacts[phone].get("nickname"):
                            existing_contacts[phone]["name"] = name
                            existing_contacts[phone]["nickname"] = name
                            updated_count += 1
                        elif existing_contacts[phone].get("nickname") and name:
                            # Keep old nickname, update real name optionally
                            if existing_contacts[phone].get("name") == "":
                                existing_contacts[phone]["name"] = name
                    else:
                        existing_contacts[phone] = {
                            "name": name,
                            "nickname": name
                        }
                        added_count += 1
                        
    # Save back
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_contacts, f, indent=2)
        
    print(f"Merge complete! Added: {added_count}, Updated existing entries: {updated_count}")
    print("Now update your UI to see the imported contacts.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_contacts.py <path_to_exported_csv>")
    else:
        merge_csv_to_contacts(sys.argv[1])
