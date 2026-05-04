# How to Use the PKB SMS Assistant

This guide covers how to set up the assistant and send your first AI-drafted SMS.

## 1. Initial Setup (API Keys)
Before using the assistant, you must configure your API keys. 
1. Run the application by executing:
   ```bash
   python main.py
   ```
2. In the top right corner of the window, click on **⚙️ Settings**.
3. Enter your **GoTo Client ID** and **GoTo Secret** (e.g. from the `Goto info.txt` template).
4. Enter your **Google Gemini API Key**.
5. Save the configuration. 

## 2. Fetching SMS History
1. Click **🔄 Refresh** (or wait for auto-load) to see your recent chats.
2. Use the **🔍 Search** bar above the list to filter by name or phone number.
3. Click a conversation row to select it. The search will automatically reset.
4. Click **📨 Load Chat** to fetch the message history.
5. Read the history to understand the context.

## 3. Drafting a Reply
1. On the right side of the screen, select the **Desired Tone** from the dropdown menu (e.g., Professional, Empathetic).
2. In the **Intent** box, type exactly what you want to convey in simple terms. Example: *"Tell the client we will push the deadline to Wednesday but need them to sign off on the design by tomorrow."*
3. Click **✨ Generate AI Reply**.
4. The draft will appear in the text box below.
5. **Local Fallback**: If "Use Paid" is enabled and your free Gemini key fails (e.g., rate limit), the app will automatically try to use a local **Ollama** instance (requires `llama3` model) before using your paid Gemini key.

## 4. Reviewing and Sending
1. Review the generated response in the **Draft Reply (Editable)** text box. 
2. Make any manual adjustments or corrections you see fit.
3. Once satisfied, click the green **Send SMS** button.
4. Check the status bar at the bottom for confirmation that the message was sent successfully.
