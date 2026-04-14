# TODO List

- [x] **GoTo API: Real Endpoints**
  Replace the mock logic in `modules/goto_api.py` with actual LogMeIn/GoTo SMS endpoints. Find the exact URLs for history retrieval and message sending.
  
- [x] **Secret Encryption**
  Find ways to encrypt the secrets file, including the google key. Since I will ship an exe file created with pyinstaller, I prefer to have a weak layer of encryption than plain text information open.

- [x] **Phone Number Validation**
  Add a regex or `phonenumbers` python package validation step before allowing a user to click "Fetch" or "Send".

- [x] **Keyboard Shortcuts**
  Allow the user to hit `Enter` inside the Intent box to trigger the Generate AI reply function.

- [x] **Unit Tests**
  Create basic test cases for the `rate_limiter.py` and `gemini_ai.py` logic.

- [x] **Error Handling**
  Expand error messaging beyond the small status bar. If GoTo API fails because the token is expired, auto-refresh the token. Catch network disconnects gracefully.

- [x] **Context Menu (Right-click)**
  Add a custom right-click context menu (secondary mouse click) to text boxes to allow users the standard OS ability to "Paste" information.
