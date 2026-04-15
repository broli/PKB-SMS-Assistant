import requests
from modules.config_manager import load_config
from modules.auth_handler import refresh_access_token
from modules import rate_limiter
from modules import contact_book


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

    def get_recent_conversations(self):
        """Fetches recent conversations sorted by latest interaction using the correct /conversations endpoint."""
        config = load_config()
        owner_number = config.get("goto_phone")
        if not owner_number:
            return {"error": "GoTo Account Phone Number missing in settings."}

        try:
            url = f"{self.base_url}/conversations"
            params = {"ownerPhoneNumber": self._clean_phone(owner_number)}
            resp = self._make_request("GET", url, params=params)
            data = resp.json()

            items = data.get("items", [])
            conversations = []
            for item in items:
                # contactPhoneNumbers is a list; grab the first entry
                contact_phones = item.get("contactPhoneNumbers", [])
                contact_phone  = contact_phones[0] if contact_phones else ""
                conversations.append({
                    "phone":            contact_phone,
                    "last_interaction": item.get("lastMessageTimestamp", ""),
                    "unread_count":     item.get("unreadMessagesCount", 0),
                    "last_message_id":  item.get("lastMessageId", ""),
                })

            # API already returns DESC by lastMessageTimestamp, but sort locally to be safe
            conversations.sort(key=lambda x: x["last_interaction"], reverse=True)
            return {"conversations": conversations}

        except requests.exceptions.RequestException as e:
            msg = f"Error fetching conversations: {e}"
            if hasattr(e, 'response') and e.response is not None:
                msg += f" | {e.response.text}"
            return {"error": msg}
        except Exception as e:
            return {"error": str(e)}

    def sync_contacts(self):
        """
        Fetches all contacts from GoTo voice-admin API and merges into local contacts.json.
        Preserves any existing local nicknames.
        Returns dict with 'count' on success or 'error' on failure.
        """
        try:
            url = "https://api.goto.com/voice-admin/v1/contacts"
            # Use _make_request to get auto token-refresh
            resp = self._make_request("GET", url)
            data = resp.json()

            # Load existing local contacts to preserve nicknames
            existing = contact_book.load_contacts()

            items = data.get("items", [])
            count = 0
            for item in items:
                phones = item.get("phoneNumbers", []) or []
                first  = item.get("firstName", "").strip()
                last   = item.get("lastName",  "").strip()
                name   = f"{first} {last}".strip() or item.get("name", "").strip()

                for phone_entry in phones:
                    # phone_entry may be a string or a dict {"number": "+1...", "type": "..."}
                    if isinstance(phone_entry, dict):
                        raw_phone = phone_entry.get("number", "")
                    else:
                        raw_phone = str(phone_entry)

                    if not raw_phone:
                        continue

                    # Normalise to E.164 (+digits) — keep existing nickname
                    digits = "".join(c for c in raw_phone if c.isdigit())
                    e164   = f"+{digits}" if digits else raw_phone

                    nickname = existing.get(e164, {}).get("nickname", "") if e164 in existing else ""
                    existing[e164] = {"name": name, "nickname": nickname}
                    count += 1

            contact_book.save_contacts(existing)
            return {"count": count, "raw_count": len(items)}

        except requests.exceptions.RequestException as e:
            msg = f"Error syncing contacts: {e}"
            if hasattr(e, 'response') and e.response is not None:
                msg += f" | {e.response.text[:200]}"
            return {"error": msg}
        except Exception as e:
            return {"error": str(e)}

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
