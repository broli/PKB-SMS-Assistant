<p align="center">
  <img src="pkb_sms_assistant_hero.png" width="800" alt="PKB SMS Assistant Banner">
</p>

# 💬 PKB SMS Assistant v2.0

**PKB SMS Assistant** is a modern, AI-powered desktop application designed to streamline SMS communication via the **GoTo Connect** platform. By leveraging the **Google Gemini Pro** model, it helps users draft professional, empathetic, and context-aware replies to client messages in seconds.

---

## ✨ Key Features

- **🤖 AI-Powered Drafting**: Generate intelligent SMS replies based on your conversation history and desired tone (Professional, Casual, Empathetic, etc.).
- **🔐 Secure GoTo Integration**: Full OAuth2 support for secure access to your GoTo Connect messaging and contact data.
- **📔 Advanced Contact Book**: 
  - Effortlessly manage local nicknames for phone numbers.
  - **Bulk Import**: Quickly sync your entire GoTo contact list via a simple copy-paste text import with a detailed safety preview.
  - **Conflict Intelligence**: Intelligent merging logic that preserves your custom nicknames while updating official names.
- **🌙 Modern Premium UI**: A sleek, dark-mode interface built with `customtkinter` for a professional desktop experience.
- **📥 Chat Export**: Export your conversation histories to clean, well-formatted Markdown files for documentation or internal review.
- **⚡ Rate Limiting**: Built-in protection to ensure smooth operation within GoTo and Google API quotas.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ 
- A GoTo Connect Developer account (for API credentials)
- A Google Gemini API Key (Free or Paid)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pkb-sms-assistant.git
   cd pkb-sms-assistant
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

---

## 🛠️ Configuration

Open the **Settings** menu within the app to configure:
- **API Keys**: Insert your Gemini API keys (Free and Paid).
- **GoTo Auth**: Follow the easy OAuth flow to link your account.
- **Custom Prompt**: Fine-tune the AI's "personality" by editing the global system prompt.

---

## 📦 Building the Executable

To generate a standalone `.exe` for Windows:

```bash
pyinstaller main.spec
```

The resulting executable will be found in the `dist/` directory.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for improved client communication.
</p>
