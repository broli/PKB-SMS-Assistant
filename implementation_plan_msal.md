# Implementation Plan: Microsoft Domain Verification (Option 1)

This plan outlines the steps to integrate Microsoft Authentication (MSAL) into the PKB SMS Assistant. The goal is to verify that the user trying to enable the "Use Paid" toggle has a valid `@company.com` Microsoft account before allowing the toggle to turn on. 

Since you will distribute the key manually and rotate it, this provides a solid layer of protection against unauthorized outsiders using the app.

## User Review Required

> [!IMPORTANT]
> To implement this, you **must** register this application in your company's Microsoft Entra ID (Azure AD) to get a `Client ID`. 
> 
> **Steps you will need to do (I assume you have admin access):**
> 1. Go to [Entra admin center](https://entra.microsoft.com/) -> App Registrations -> New Registration.
> 2. Name: "PKB SMS Assistant".
> 3. Supported account types: "Accounts in this organizational directory only (Single tenant)".
> 4. Redirect URI: Select "Public client/native (mobile & desktop)" and set the URI to `http://localhost`.
> 5. Once created, you will get an **Application (client) ID** and a **Directory (tenant) ID**. I will need these values, or I can add fields in the Settings window for you to input them later. **Please let me know if you want them hardcoded or added to settings.**

## Proposed Changes

---

### Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/carlo/Desktop/Programing/Python/PKB%20SMS%20Assistant/requirements.txt)
- Add `msal` library (Microsoft Authentication Library) to handle the OAuth flow and token retrieval.

---

### Configuration Management

#### [MODIFY] [config_manager.py](file:///c:/Users/carlo/Desktop/Programing/Python/PKB%20SMS%20Assistant/modules/config_manager.py)
- Update `load_config` to include default values for `microsoft_client_id`, `microsoft_tenant_id`, and `company_domain`. 
- (We can hardcode the `company_domain` later, but storing it in config makes the app more flexible).

#### [MODIFY] [settings_window.py](file:///c:/Users/carlo/Desktop/Programing/Python/PKB%20SMS%20Assistant/ui/settings_window.py)
- Add entries for the Microsoft Entra `Client ID`, `Tenant ID` (optional, can use 'common'), and the required `Company Domain` (e.g., `yourcompany.com`).

---

### Authentication Logic

#### [NEW] `modules/msal_auth.py`
- Create a new file to handle Microsoft Login.
- Implement `verify_company_employee(client_id, authority, required_domain)`:
    - Uses `msal.PublicClientApplication`.
    - Initiates `acquire_token_interactive()` which opens the browser for Microsoft login.
    - Extracts the `preferred_username` (email) from the returned token.
    - Returns `True` if the email ends with the `required_domain`, and `False` otherwise.

---

### Main UI Logic

#### [MODIFY] [main_window.py](file:///c:/Users/carlo/Desktop/Programing/Python/PKB%20SMS%20Assistant/ui/main_window.py)
- Update the `use_paid_switch` command parameter to trigger a verification function when toggled.
- **Toggle Logic**:
    - If the user switches "Use Paid" from OFF to ON:
        - Temporarily disable the switch.
        - Update status: "Verifying Microsoft Identity..."
        - Call `msal_auth.verify_company_employee(...)`.
        - If verification succeeds: Leave the toggle ON, update status "Verified Employee."
        - If verification fails or is canceled: Force the toggle back to OFF, update status "Verification failed: Invalid domain."
    - If the user switches from ON to OFF: Just turn it off.

---

## Verification Plan

### Manual Verification
1. Open settings, input the Client ID, Tenant ID, and company domain (e.g., `mycompany.com`).
2. Toggle "Use Paid".
3. A Microsoft login popup should appear.
4. Log in with a valid `@mycompany.com` account -> Toggle stays ON.
5. Restart the app, clear token cache (if we implement persistent caching) or use a private window, try logging in with a `@gmail.com` or other domain -> Toggle gracefully switches back OFF with an error message.
