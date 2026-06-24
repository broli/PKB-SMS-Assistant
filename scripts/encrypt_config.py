import json
from cryptography.fernet import Fernet
import base64
import os

def main():
    print("=== Corporate Config Encryptor ===")
    
    # 1. Generate or use an existing key
    print("If you already have a Fernet decryption key (e.g. from corporate_secrets.py), paste it below.")
    print("Otherwise, leave blank to generate a new one.")
    key_input = input("Encryption Key: ").strip()
    
    if not key_input:
        key = Fernet.generate_key()
        print(f"\n[NEW KEY GENERATED] Save this in corporate_secrets.py: {key.decode('utf-8')}\n")
    else:
        # Validate format
        try:
            key = key_input.encode('utf-8')
            Fernet(key)
        except ValueError:
            print("Invalid Fernet key format.")
            return

    cipher_suite = Fernet(key)
    
    # 2. Ask for the config values
    gemini_key = input("Enter Gemini API Key: ").strip()
    m365_client = input("Enter Microsoft 365 Client ID: ").strip()
    m365_tenant = input("Enter Microsoft 365 Tenant ID: ").strip()
    
    config_dict = {
        "gemini_api_key": gemini_key,
        "m365_client_id": m365_client,
        "m365_tenant_id": m365_tenant
    }
    
    payload = json.dumps(config_dict).encode('utf-8')
    encrypted_payload = cipher_suite.encrypt(payload)
    
    # 3. Save to file
    out_file = "corporate_config.tmp"
    with open(out_file, "wb") as f:
        f.write(encrypted_payload)
        
    print(f"\nSuccess! Encrypted configuration saved to: {os.path.abspath(out_file)}")
    print("Upload this file to your SharePoint link.")

if __name__ == "__main__":
    main()
