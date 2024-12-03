import datetime

from dfdatetime import posix_time as dfdatetime_posix_time
from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface

class IOSRoutinedEventData(events.EventData):
    """Event data for com.apple.routined plist.

    Attributes:
        key (str): Name of the key.
        value (str): Value associated with the key.
    """
    DATA_TYPE = 'ios:routined:entry'

    def __init__(self):
        """Initializes event data."""
        super(IOSRoutinedEventData, self).__init__(data_type=self.DATA_TYPE)
        self.key = None
        self.value = None

class IOSRoutinedPlistPlugin(interface.PlistPlugin):
    """Plist parser plugin for com.apple.routined plist."""

    NAME = 'ios_routined'
    DATA_FORMAT = 'Apple iOS Routined plist file'

    PLIST_PATH_FILTERS = frozenset([
        interface.PlistPathFilter('com.apple.routined.plist')
    ])

    PLIST_KEYS = frozenset([
        'XPCActivityLastAttemptDate.com.apple.routined.assets',
    ])

    def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
        """Extract data from the plist.

        Args:
            parser_mediator (ParserMediator): mediates interactions between parsers and other components.
            match (Optional[dict[str, object]]): keys extracted from PLIST_KEYS.
        """
        for key, value in match.items():
            event_data = IOSRoutinedEventData()
            event_data.key = key

            if isinstance(value, datetime.datetime):
                timestamp = int(value.timestamp() * definitions.NANOSECONDS_PER_SECOND)
                event_data.value = dfdatetime_posix_time.PosixTimeInNanoseconds(
                    timestamp=timestamp)
            else:
                event_data.value = value

            parser_mediator.ProduceEventData(event_data)

plist.PlistParser.RegisterPlugin(IOSRoutinedPlistPlugin)
