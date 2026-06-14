import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import datetime

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
