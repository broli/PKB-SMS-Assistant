from cryptography.fernet import Fernet
import os

def generate_key_and_encrypt():
    print("=== Google API Key Encryptor ===")
    api_key = input("Paste your Google API Key (plain text): ").strip()
    
    if not api_key:
        print("Error: API Key cannot be empty.")
        return

    # Generate a random encryption key
    encryption_key = Fernet.generate_key()
    cipher_suite = Fernet(encryption_key)
    
    # Encrypt the API key
    encrypted_payload = cipher_suite.encrypt(api_key.encode('utf-8'))
    
    # Write the encrypted payload to a file
    with open("encrypted_key.txt", "wb") as f:
        f.write(encrypted_payload)
    
    print("\nSUCCESS!")
    print("1. An 'encrypted_key.txt' file has been created in this folder.")
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
