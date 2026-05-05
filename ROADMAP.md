# Project Roadmap

The following outlines the phased development goals for the PKB SMS Assistant.

## Phase 1: Core UI and Mock Integration (Completed)
- [x] Basic CustomTkinter layout (2-column design)
- [x] Settings window for API Keys management
- [x] Google Gemini integration for prompt drafting
- [x] Mock implementations of GoTo API logic
- [x] Rate limiter module

## Phase 2: Live GoTo Integration (Completed)
- [x] Implement the real GoTo Authentication OAuth token flow
- [x] Connect the `get_sms_history` endpoint for live phone numbers
- [x] Connect the `send_sms` endpoint to broadcast messages
- [x] **New**: Added Conversation Search and Filtering
- [x] **New**: Local Ollama (llama3) Fallback Integration
- [x] **New**: Optimized 10s cooldowns for smoother UX
- [x] **New**: Fixed Linux/Wayland UI scaling artifacts (v2.3)

## Phase 3: Qt Migration & Architectural Rewrite (Completed - v3.0)
- [x] **PySide6 Migration**: Replaced CustomTkinter with Qt for native Linux/Wayland support.
- [x] **Signals & Slots**: Re-implemented all background tasks using thread-safe Qt Signals.
- [x] **Separation of Concerns**: Extracted threading logic into dedicated `ui/qt_workers.py`.
- [x] **Native Aesthetics**: Adopted "Fusion" styling for a clean, professional cross-platform look.
- [x] **Global Scaling**: Integrated reliable DPI scaling for high-resolution displays.

## Phase 4: Data Persistence & Advanced Features (Current)
- [ ] **Data persistence**: Displaying last used phone numbers and session state.
- [ ] **SQLite Caching**: Local storage of previous conversations to minimize GoTo API calls.
- [ ] **Logging**: Implement local app logging to track errors without console noise.
- [ ] **Validation**: Better E.164 phone number compliance checking.

## Phase 5: Advanced Intelligence
- [ ] **Context Awareness**: Incorporate project contexts directly into Gemini prompts (e.g., status docs).
- [ ] **Multi-Tab Interface**: Support multiple ongoing conversation tabs simultaneously.

## Phase 6: Distribution
- [x] **Build Scripts**: Updated `main.spec` for PySide6 compatibility.
- [ ] Standalone installer creation (InnoSetup).
