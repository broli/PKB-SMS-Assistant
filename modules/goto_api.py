import requests
from modules.config_manager import load_config
from modules.auth_handler import refresh_access_token
from modules import rate_limiter

class GoToAPI:
    def __init__(self):
        self.base_url = "https://api.goto.com/messaging/v1"

    def _get_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _make_request(self, method, url, params=None, json_data=None):
        config = load_config()
        token = config.get("access_token")
        
        if not token:
            raise Exception("GoTo Access Token missing. Please log in from Settings.")
            
        kwargs = {"headers": self._get_headers(token)}
        if params: kwargs["params"] = params
        if json_data: kwargs["json"] = json_data
            
        resp = requests.request(method, url, **kwargs)
        
        if resp.status_code == 401:
            # Token might be expired, try refreshing once
            if refresh_access_token():
                config = load_config()
                token = config.get("access_token")
                kwargs["headers"] = self._get_headers(token)
                resp = requests.request(method, url, **kwargs)
                
        resp.raise_for_status()
        return resp

    def _clean_phone(self, phone_str):
        if not phone_str:
            return ""
        return "".join(c for c in phone_str if c.isdigit())

    def _phones_match(self, p1, p2):
        """Robust comparison of two phone numbers by comparing their last 10 digits."""
        c1 = self._clean_phone(p1)
        c2 = self._clean_phone(p2)
        if not c1 or not c2:
            return False
        return c1[-10:] == c2[-10:]

    def get_sms_history(self, phone_number):
        """Fetches SMS history and returns a list of message dicts."""
        config = load_config()
        owner_number = config.get("goto_phone")
        if not owner_number:
            return [{"body": "Error: GoTo Account Phone Number missing in settings.", "is_user": False}]
            
        try:
            url = f"{self.base_url}/messages"
            params = {
                "ownerPhoneNumber": self._clean_phone(owner_number),
                "contactPhoneNumber": self._clean_phone(phone_number)
            }
            resp = self._make_request("GET", url, params=params)
            data = resp.json()
            
            items = data.get("items", [])
            items = sorted(items, key=lambda x: x.get("timestamp", "") or x.get("createdAt", ""))
            
            history_list = []
            for msg in items:
                # GoTo API returns direction as 'OUT' or 'IN'
                direction = msg.get("direction", "").upper()
                author = msg.get("authorPhoneNumber", "")
                
                is_user = False
                if direction == "OUT":
                    is_user = True
                elif direction == "IN":
                    is_user = False
                elif author and self._phones_match(author, owner_number):
                    is_user = True
                
                history_list.append({
                    "body": msg.get("body", ""),
                    "is_user": is_user
                })
                
            if history_list:
                rate_limiter.record_goto_call()
                return history_list
            return [{"body": "No chat history retrieved.", "is_user": False}]
            
        except requests.exceptions.RequestException as e:
            msg = f"Error fetching from GoTo API: {e}"
            if hasattr(e, 'response') and e.response is not None:
                msg += f"\nResponse: {e.response.text}"
            return [{"body": msg, "is_user": False}]
        except Exception as e:
            return [{"body": f"Error: {e}", "is_user": False}]


    def send_sms(self, phone_number, message):
        """Sends an SMS using GoTo API."""
        config = load_config()
        owner_number = config.get("goto_phone")
        if not owner_number:
            print("Missing owner number.")
            return False
            
        try:
            url = f"{self.base_url}/messages"
            payload = {
                "ownerPhoneNumber": self._clean_phone(owner_number),
                "contactPhoneNumbers": [self._clean_phone(phone_number)],
                "body": message
            }
            self._make_request("POST", url, json_data=payload)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending SMS: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
