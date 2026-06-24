import gi
import datetime
gi.require_version("EDataServer", "1.2")
gi.require_version("ECal", "2.0")
gi.require_version("ICalGLib", "4.0")
from gi.repository import EDataServer, ECal, ICalGLib

registry = EDataServer.SourceRegistry.new_sync(None)
source = registry.ref_default_calendar()
client = ECal.Client.connect_sync(source, ECal.ClientSourceType.EVENTS, 30, None)

ical_str_vcal = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PKB SMS Assistant//EN
BEGIN:VEVENT
UID:sms-assistant-event-1234567
DTSTAMP:20260605T120000Z
DTSTART:20260605T120000Z
DTEND:20260605T130000Z
SUMMARY:Test event with vcalendar
END:VEVENT
END:VCALENDAR"""

try:
    comp1 = ICalGLib.Component.new_from_string(ical_str_vcal)
    client.create_object_sync(comp1, ECal.OperationFlags.NONE, None)
    print("Success VCALENDAR!")
except Exception as e:
    print("Error VCALENDAR:", e)

ical_str_vevent = """BEGIN:VEVENT
UID:sms-assistant-event-1234568
DTSTAMP:20260605T120000Z
DTSTART:20260605T120000Z
DTEND:20260605T130000Z
SUMMARY:Test event without vcalendar
END:VEVENT"""

try:
    comp2 = ICalGLib.Component.new_from_string(ical_str_vevent)
    client.create_object_sync(comp2, ECal.OperationFlags.NONE, None)
    print("Success VEVENT!")
except Exception as e:
    print("Error VEVENT:", e)
