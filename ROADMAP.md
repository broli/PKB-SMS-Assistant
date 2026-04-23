# Project Roadmap

The following outlines the phased development goals for the PKB SMS Assistant.

## Phase 1: Core UI and Mock Integration (Completed)
- [x] Basic CustomTkinter layout (2-column design)
- [x] Settings window for API Keys management
- [x] Google Gemini integration for prompt drafting
- [x] Mock implementations of GoTo API logic
- [x] Rate limiter module

## Phase 2: Live GoTo Integration (Current)
- [x] Implement the real GoTo Authentication OAuth token flow
- [x] Connect the `get_sms_history` endpoint for live phone numbers
- [x] Connect the `send_sms` endpoint to broadcast messages
- [x] **New**: Added Conversation Search and Filtering
- [x] **New**: Local Ollama (llama3) Fallback Integration
- [x] **New**: Optimized 10s cooldowns for smoother UX

## Phase 3: Enhanced Stability & Feedback
- [ ] Add loading spinners and improved GUI blocking during threaded API calls
- [ ] Implement local app logging to track errors without printing to console
- [ ] Better validation of phone number formats (E.164 compliance)
- [ ] Data persistence: Displaying last used phone numbers 

## Phase 4: Advanced Features
- [ ] Multiple ongoing conversation tabs
- [ ] Incorporate project contexts directly into the Gemini prompt (e.g., feeding the AI a PDF of the client's current project status)
- [ ] Local storage (SQLite) caching of previous conversations to minimize GoTo API trips

## Phase 5: Distribution
- [ ] Package the application into a standalone `.exe` using PyInstaller
- [ ] Create an application icon and installer using InnoSetup
