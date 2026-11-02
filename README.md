<p align="center">
  <img src="pkb_sms_assistant_hero.png" width="800" alt="PKB SMS Assistant Banner">
</p>

# PKB SMS Assistant v3.0

**PKB SMS Assistant** is a desktop application built with **PySide6 (Qt)** to manage and streamline SMS communication via the **GoTo Connect** platform. It integrates with **Google Gemini** to help users draft context-aware replies based on message history, tone, and intent.

---

## Key Features

- **AI-Powered Drafting**: Generate draft replies based on conversation history and selected tone (Professional, Casual, Empathetic, etc.).
- **GoTo Integration**: OAuth2 support for GoTo Connect messaging and contact data.
- **Contact Book Management**: 
  - Manage local nicknames for phone numbers.
  - **Bulk Import**: Import GoTo contact text dumps with preview verification.
  - **Nickname Preservation**: Merges official names from imports without overwriting local custom nicknames.
- **Search**: Real-time filtering of recent conversations by name or phone number.
- **Local AI Fallback (Ollama)**: Automatic fallback to a local **Ollama** instance (`llama3`) when Gemini is unavailable or rate-limited.
- **Rate Limiting**: Configured cooldown periods to prevent API quota exhaustion on external services.
- **Chat Export**: Export conversation histories to formatted Markdown files.

For upcoming features and development plans, see [ROADMAP](docs/ROADMAP.md).

---

## Quick Start

### Prerequisites

- Python 3.10+
- A GoTo Connect Developer account (for OAuth API credentials)
- A Google Gemini API Key (Free or Paid)
- **Linux only**: System libraries required for Evolution calendar bindings (`sudo apt install libgirepository1.0-dev libcairo2-dev pkg-config`)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/broli/PKB-SMS-Assistant.git
   cd PKB-SMS-Assistant
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

## Configuration

Open the **Settings** dialog in the application to configure:
- **API Keys**: Configure Gemini API keys (Free and Paid tiers).
- **Local AI**: Ensure **Ollama** is running on `localhost:11434` with `llama3` for offline fallback.
- **GoTo Auth**: Authenticate using the OAuth flow to link your account.
- **Custom Prompt**: Customize the system prompt used for AI response generation.

---

## Building Standalone Binaries

- **Linux**: Run `pyinstaller main.spec` (or `./build.sh`)
- **Windows**: Run `pyinstaller windows_build.spec` (or `.\build.ps1` in PowerShell)

The compiled executable is written to the `dist/` directory.

---

## Documentation

Additional setup guides and technical references are located in `docs/`:
- [How to Use the Assistant](docs/HOW_TO_USE.md)
- [Feature Walkthrough](docs/walkthrough.md)
- [Windows Build Instructions](docs/windows_build_instructions.md)
- [Project Roadmap](docs/ROADMAP.md)

---

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
