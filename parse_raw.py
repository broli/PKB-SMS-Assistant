import json

def clean_phone(raw_phone):
    digits = "".join(c for c in raw_phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) >= 11:
        return f"+{digits}"
    return None

def main():
    try:
        with open("contacts.json", "r", encoding="utf-8") as f:
            contacts = json.load(f)
    except FileNotFoundError:
        contacts = {}

    with open("raw_contacts.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    count = 0
    for i, line in enumerate(lines):
        if line.lower() == "private" or line.lower() == "shared" or line.lower() == "company":
            name = lines[i-1] if i > 0 else ""
            if name in ["Name", "Type", "Phone number", "Email address", "--"]:
                continue
            
            if i+1 < len(lines):
                phone_raw = lines[i+1]
                if phone_raw == "--" or "@" in phone_raw:
                    continue
                
                phone = clean_phone(phone_raw)
                if not phone:
                    continue
                
                if phone not in contacts:
                    contacts[phone] = {"name": name, "nickname": name}
                    count += 1
                else:
                    if not contacts[phone].get("name") and not contacts[phone].get("nickname"):
                        contacts[phone]["name"] = name
                        contacts[phone]["nickname"] = name
                    elif contacts[phone].get("nickname") and name:
                        if not contacts[phone].get("name"):
                            contacts[phone]["name"] = name

    with open("contacts.json", "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)

    print(f"Successfully scraped and merged {count} new contacts into contacts.json!")

if __name__ == "__main__":
    main()
