import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import datetime
import os
import requests
import json
try:
    import msal
except ImportError:
    msal = None
class CalendarProvider(ABC):
    """Abstract base class for all calendar/task synchronization providers."""
    
    @abstractmethod
    def add_event(self, summary: str, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        """Adds an event to the calendar."""
        pass
        
    @abstractmethod
    def add_task(self, summary: str, due_date: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        """Adds a task/to-do item."""
        pass


class EvolutionProvider(CalendarProvider):
    """
    Implementation of CalendarProvider that uses GNOME Evolution (EDataServer via gi)
    to silently insert events and tasks.
    """
    def __init__(self):
        try:
            import gi
            gi.require_version("EDataServer", "1.2")
            gi.require_version("ECal", "2.0")
            gi.require_version("ICalGLib", "4.0")
            from gi.repository import EDataServer, ECal, ICalGLib
            self.EDataServer = EDataServer
            self.ECal = ECal
            self.ICalGLib = ICalGLib
            
            self.registry = self.EDataServer.SourceRegistry.new_sync(None)
            self._connected = True
        except ImportError as e:
            logging.error(f"Failed to load Evolution gi bindings: {e}")
            self._connected = False

    def _get_client(self, source_type):
        if not self._connected:
            return None
        
        # Get default source for the given type
        if source_type == self.ECal.ClientSourceType.EVENTS:
            source = self.registry.ref_default_calendar()
        elif source_type == self.ECal.ClientSourceType.TASKS:
            source = self.registry.ref_default_task_list()
        else:
            source = None
            
        if not source:
            logging.warning("No default Evolution calendar/task source found.")
            return None
            
        try:
            # wait_for_connected_seconds=30
            client = self.ECal.Client.connect_sync(source, source_type, 30, None)
            return client
        except Exception as e:
            logging.error(f"Failed to connect to Evolution calendar client: {e}")
            return None


    def add_event(self, summary: str, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        if not self._connected:
            return False
            
        if not end_time:
            end_time = start_time + datetime.timedelta(hours=1)
            
        client = self._get_client(self.ECal.ClientSourceType.EVENTS)
        if not client:
            return False
            
        # Create unique UID
        uid = f"sms-assistant-{int(datetime.datetime.now().timestamp())}"
        dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        if timezone != "Local":
            try:
                import zoneinfo
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
                start_time = start_time.astimezone(datetime.timezone.utc)
                dtstart = start_time.strftime("%Y%m%dT%H%M%SZ")
                
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
                end_time = end_time.astimezone(datetime.timezone.utc)
                dtend = end_time.strftime("%Y%m%dT%H%M%SZ")
            except Exception as e:
                logging.error(f"Timezone conversion error: {e}")
                dtstart = start_time.strftime("%Y%m%dT%H%M%S")
                dtend = end_time.strftime("%Y%m%dT%H%M%S")
        else:
            dtstart = start_time.strftime("%Y%m%dT%H%M%S")
            dtend = end_time.strftime("%Y%m%dT%H%M%S")
        
        ical_str = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
END:VEVENT"""

        try:
            comp = self.ICalGLib.Component.new_from_string(ical_str)
            client.create_object_sync(comp, self.ECal.OperationFlags.NONE, None)
            logging.info(f"Successfully added event to Evolution: {summary}")
            return True
        except Exception as e:
            logging.error(f"Error adding event to Evolution: {e}")
            return False

    def add_task(self, summary: str, due_date: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        if not self._connected:
            return False
            
        client = self._get_client(self.ECal.ClientSourceType.TASKS)
        if not client:
            return False
            
        uid = f"sms-assistant-task-{int(datetime.datetime.now().timestamp())}"
        dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        ical_str = f"""BEGIN:VTODO
UID:{uid}
DTSTAMP:{dtstamp}
SUMMARY:{summary}"""

        if due_date:
            if timezone != "Local":
                try:
                    import zoneinfo
                    if due_date.tzinfo is None:
                        due_date = due_date.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
                    due_date = due_date.astimezone(datetime.timezone.utc)
                    due_str = due_date.strftime("%Y%m%dT%H%M%SZ")
                except Exception as e:
                    logging.error(f"Timezone conversion error: {e}")
                    due_str = due_date.strftime("%Y%m%dT%H%M%S")
            else:
                due_str = due_date.strftime("%Y%m%dT%H%M%S")
            ical_str += f"\nDUE:{due_str}"
            
        ical_str += "\nEND:VTODO"

        try:
            comp = self.ICalGLib.Component.new_from_string(ical_str)
            client.create_object_sync(comp, self.ECal.OperationFlags.NONE, None)
            logging.info(f"Successfully added task to Evolution: {summary}")
            return True
        except Exception as e:
            logging.error(f"Error adding task to Evolution: {e}")
            return False

class M365Provider(CalendarProvider):
    def __init__(self, client_id: str, tenant_id: str, auth_callback=None):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.auth_callback = auth_callback
        self.authority = f"https://login.microsoftonline.com/{tenant_id}" if tenant_id else ""
        self.scopes = ["Calendars.ReadWrite", "Tasks.ReadWrite"]
        self.cache = None
        self.cache_file = os.path.join(os.path.expanduser("~"), ".m365_token.bin")
        self.app = None
        
        if msal:
            self.cache = msal.SerializableTokenCache()
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, "r") as f:
                        self.cache.deserialize(f.read())
                except Exception as e:
                    logging.error(f"Failed to load msal cache: {e}")
                    
            if self.client_id and self.tenant_id:
                self.app = msal.PublicClientApplication(
                    self.client_id, 
                    authority=self.authority,
                    token_cache=self.cache
                )

    def _ensure_app_initialized(self):
        if not self.client_id or not self.tenant_id:
            if self.auth_callback:
                logging.info("M365 credentials missing. Triggering auth callback...")
                if self.auth_callback():
                    from modules import config_manager
                    self.client_id = config_manager._RUNTIME_OVERRIDES.get("m365_client_id", "")
                    self.tenant_id = config_manager._RUNTIME_OVERRIDES.get("m365_tenant_id", "")
                    self.authority = f"https://login.microsoftonline.com/{self.tenant_id}" if self.tenant_id else ""
        
        if self.client_id and self.tenant_id and not self.app and msal:
            self.app = msal.PublicClientApplication(
                self.client_id, 
                authority=self.authority,
                token_cache=self.cache
            )

    def _get_token(self):
        if not msal:
            logging.error("MSAL library is not installed.")
            return None
            
        self._ensure_app_initialized()
        
        if not self.app:
            logging.error("MSAL app is not configured. Missing credentials?")
            return None
            
        if not self.client_id or not self.tenant_id:
            logging.error("M365 credentials missing in settings.")
            return None
            
        accounts = self.app.get_accounts()
        result = None
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            
        if not result:
            logging.info("No suitable token exists in cache. Acquiring new one interactively.")
            result = self.app.acquire_token_interactive(scopes=self.scopes)
            
        if result and "access_token" in result:
            try:
                with open(self.cache_file, "w") as f:
                    f.write(self.cache.serialize())
            except Exception as e:
                logging.error(f"Failed to save msal cache: {e}")
            return result["access_token"]
        else:
            logging.error(f"Failed to acquire token: {result.get('error') if result else 'Unknown error'}")
            return None

    def add_event(self, summary: str, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        token = self._get_token()
        if not token:
            return False
            
        if not end_time:
            end_time = start_time + datetime.timedelta(hours=1)
            
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        
        try:
            import zoneinfo
            if timezone != "Local" and start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
                end_time = end_time.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
            
            start_time = start_time.astimezone(datetime.timezone.utc)
            end_time = end_time.astimezone(datetime.timezone.utc)
        except Exception:
            pass

        event = {
            "subject": summary,
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC"
            }
        }

        endpoint = "https://graph.microsoft.com/v1.0/me/events"
        try:
            response = requests.post(endpoint, headers=headers, json=event)
            if response.status_code == 201:
                logging.info(f"Successfully added event to M365: {summary}")
                return True
            else:
                logging.error(f"Error adding event to M365: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Network error adding event to M365: {e}")
            return False

    def add_task(self, summary: str, due_date: Optional[datetime.datetime] = None, timezone: str = "Local") -> bool:
        token = self._get_token()
        if not token:
            return False

        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        
        try:
            lists_response = requests.get("https://graph.microsoft.com/v1.0/me/todo/lists", headers=headers)
            if lists_response.status_code != 200:
                logging.error(f"Failed to get To Do lists: {lists_response.text}")
                return False
                
            lists = lists_response.json().get('value', [])
            if not lists:
                logging.error("No To Do lists found.")
                return False
                
            task_list_id = lists[0]['id']
            for l in lists:
                if l.get('displayName', '').lower() == 'tasks':
                    task_list_id = l['id']
                    break

            task_payload = {
                "title": summary
            }
            
            if due_date:
                try:
                    import zoneinfo
                    if timezone != "Local" and due_date.tzinfo is None:
                        due_date = due_date.replace(tzinfo=zoneinfo.ZoneInfo(timezone))
                    due_date = due_date.astimezone(datetime.timezone.utc)
                except Exception:
                    pass
                    
                task_payload["dueDateTime"] = {
                    "dateTime": due_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC"
                }

            endpoint = f"https://graph.microsoft.com/v1.0/me/todo/lists/{task_list_id}/tasks"
            response = requests.post(endpoint, headers=headers, json=task_payload)
            
            if response.status_code == 201:
                logging.info(f"Successfully added task to M365: {summary}")
                return True
            else:
                logging.error(f"Error adding task to M365: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Network error adding task to M365: {e}")
            return False

