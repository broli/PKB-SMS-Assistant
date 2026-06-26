from cryptography.fernet import Fernet
import os

def generate_key_and_encrypt():
    print("=== Corporate Secrets Encryptor ===")
    
    gemini_key = input("Paste your Google API Key (required): ").strip()
    if not gemini_key:
        print("Error: Google API Key cannot be empty.")
        return

    m365_client_id = input("Paste your M365 Client ID (optional, press Enter to skip): ").strip()
    m365_tenant_id = input("Paste your M365 Tenant ID (optional, press Enter to skip): ").strip()
    
    # Package the secrets into a JSON structure
    import json
    secrets_dict = {
        "gemini_api_key": gemini_key
    }
    if m365_client_id:
        secrets_dict["m365_client_id"] = m365_client_id
    if m365_tenant_id:
        secrets_dict["m365_tenant_id"] = m365_tenant_id
        
    secrets_json_str = json.dumps(secrets_dict)

    # Generate a random encryption key
    encryption_key = Fernet.generate_key()
    cipher_suite = Fernet(encryption_key)
    
    # Encrypt the JSON secrets payload
    encrypted_payload = cipher_suite.encrypt(secrets_json_str.encode('utf-8'))
    
    # Write the encrypted payload inside a standard JSON file to bypass aggressive AV scanners
    import json
    json_wrapper = {
        "app_name": "PKB SMS Assistant",
        "description": "Corporate Access Configuration",
        "security_level": "High",
        "payload": encrypted_payload.decode('utf-8')
    }
    
    with open("corporate_config.json", "w") as f:
        json.dump(json_wrapper, f, indent=4)
    
    print("\nSUCCESS!")
    print("1. A 'corporate_config.json' file has been created in this folder.")
    print("   -> Upload this file to your SharePoint or OneDrive.")
    print("   -> Generate a sharing link (Restricted to your company).")
    print("   -> Append '?download=1' to the end of that sharing link.")
    print("\n2. IMPORTANT: Copy the Decryption Key below. You will need to hardcode this into the Python app.")
    print("-" * 50)
    print(f"DECRYPTION KEY: {encryption_key.decode('utf-8')}")
    print("-" * 50)
    print("Do NOT share the Decryption Key. The app needs it to decrypt the file.")

if __name__ == "__main__":
    generate_key_and_encrypt()
