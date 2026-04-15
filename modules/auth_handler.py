import http.server
import socketserver
import urllib.parse
import webbrowser
import requests
import base64
from modules.config_manager import save_config, load_config

# GoTo OAuth Endpoints
AUTHORIZE_URL = "https://authentication.logmeininc.com/oauth/authorize"
TOKEN_URL = "https://authentication.logmeininc.com/oauth/token"

# These should match what is registered in the GoTo Developer Portal
CLIENT_ID = "85cf3392-e4fc-490e-a815-82f2ee0464dd"
CLIENT_SECRET = "zHqIlsg5Z05E4Jy2CuJwW8px"
REDIRECT_URI = "http://localhost:8080/callback"

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        if 'code' in query_components:
            auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Login Successful!</h1><p>You can close this window and return to the app.</p></body></html>")
            self.server.auth_code = auth_code
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Login Failed.</h1><p>No authorization code found.</p></body></html>")
            self.server.auth_code = None

    def log_message(self, format, *args):
        # Suppress logging
        pass

def start_oauth_flow():
    """
    Opens the default browser, starts a local server to catch the callback,
    exchanges the code for tokens, and saves them.
    Returns True if successful, False otherwise.
    """
    SCOPES = "messaging.v1.read messaging.v1.send voice-admin.v1.read"

    auth_url = (
        f"{AUTHORIZE_URL}"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )

    
    # Start local server on port 8080
    port = 8080
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    try:
        httpd = ReusableTCPServer(("", port), OAuthCallbackHandler)
    except Exception as e:
        print(f"Failed to start local server on port {port}: {e}")
        return False
        
    httpd.auth_code = None
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for exactly one request
    print("Waiting for user to authenticate via browser...")
    httpd.handle_request()
    
    auth_code = httpd.auth_code
    httpd.server_close()
    
    if auth_code:
        return exchange_code_for_token(auth_code)
    return False

def exchange_code_for_token(auth_code):
    """Exchanges the authorization code for an access token."""
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        
        # Save to config
        config = load_config()
        config["access_token"] = tokens.get("access_token")
        config["refresh_token"] = tokens.get("refresh_token")
        # Ensure we remove the old PAT
        if "goto_token" in config:
            del config["goto_token"]
        
        save_config(config)
        return True
    except Exception as e:
        print(f"Failed to exchange code for token: {e}")
        return False

def refresh_access_token():
    """Uses the stored refresh token to get a new access token."""
    config = load_config()
    refresh_token = config.get("refresh_token")
    if not refresh_token:
        return False
        
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        
        config["access_token"] = tokens.get("access_token")
        # Sometimes refresh tokens are also rotated, save it if provided
        if "refresh_token" in tokens:
            config["refresh_token"] = tokens.get("refresh_token")
            
        save_config(config)
        return True
    except Exception as e:
        print(f"Failed to refresh token: {e}")
        return False
