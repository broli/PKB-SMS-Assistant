# How to Create the Corporate Secrets File

Follow these steps to generate the encrypted configuration file containing the Corporate Gemini API Key and Microsoft 365 IDs:

### 1. Run the Encryption Script
Open your terminal and run the helper script:
```bash
python scripts/encrypt_config.py
```

### 2. Enter Your Secrets
The script will prompt you for the following information:
- **Encryption Key**: If you already have a decryption key set in `ui/settings_window.py`, paste it here. Otherwise, leave it blank to generate a new one.
- **Paid Gemini API Key**: Your corporate Gemini key.
- **Microsoft 365 Client ID**: The Client ID from your Azure App Registration.
- **Microsoft 365 Tenant ID**: The Tenant ID from your Azure App Registration.

The script will generate a new encrypted file called `corporate_config.tmp`.

### 3. Upload to SharePoint/OneDrive
Take the newly generated `corporate_config.tmp` file and upload it to your company SharePoint or OneDrive.
Create a Sharing Link set to **"People in [Company] can view"**.
**Important:** Add `?download=1` to the very end of that link.

### 4. Update the App Settings
Open `ui/settings_window.py` in your code editor. Inside the `sync_corporate_key` function, you will see:
```python
        # --- AUTHENTICATION SETTINGS ---
        # Paste your SharePoint link and Decryption Key here:
        AUTH_DOWNLOAD_URL = "YOUR_SHAREPOINT_LINK_HERE?download=1" 
        DECRYPTION_KEY = b"YOUR_DECRYPTION_KEY_HERE"
```
Paste your SharePoint link (with the `?download=1`) and the Decryption Key you got from step 2. You only have to do this once!
