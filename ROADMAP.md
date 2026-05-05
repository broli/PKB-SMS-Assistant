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

## Phase 3: Microsoft Ecosystem Integration & Security
- [ ] Implement Microsoft OAuth 2.0 Authentication (Company Account required)
- [ ] **Secure Secret Management**: Host the Client Secret and token exchange on a Microsoft Serverless (Azure Function) backend
- [ ] **Secure Gemini Proxy**: Route Gemini API calls through the serverless backend to keep the paid API key hidden from clients
- [ ] Client Proxy Logic: App requests tokens and AI completions from the serverless backend instead of storing secrets locally

## Phase 4: Team Deployment & Enterprise Readiness
- [ ] **Centralized Logging**: Integrate Azure Application Insights to monitor team usage and errors
- [ ] **Auto-Update Mechanism**: Implement a version check system to push updates to the team automatically
- [ ] **Advanced Validation**: Better validation of phone number formats (E.164 compliance)
- [ ] **Enterprise Installer**: Create an application icon and MSI installer using InnoSetup for easy distribution

## Phase 5: Misc Improvements
- [ ] Add loading spinners and improved GUI blocking during threaded API calls
- [ ] Local storage (SQLite) caching of previous conversations to minimize API trips
