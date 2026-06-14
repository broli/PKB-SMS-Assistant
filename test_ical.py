import gi
import datetime
gi.require_version("ICalGLib", "4.0")
from gi.repository import ICalGLib

uid = f"sms-assistant-task-12345"
dtstamp = "20260605T120000Z"
summary = "Test summary"
due_str = "20260605T130000Z"

ical_str = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PKB SMS Assistant//EN
BEGIN:VTODO
UID:{uid}
DTSTAMP:{dtstamp}
SUMMARY:{summary}
DUE:{due_str}
END:VTODO
END:VCALENDAR"""

print(ical_str)
try:
    comp = ICalGLib.Component.new_from_string(ical_str)
    print("Valid!", comp.is_valid())
except Exception as e:
    print("Invalid!", e)
