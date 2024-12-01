# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS routined application plist files.

The plist contains various routine-related information, including task history,
account details, timestamps for asset updates, and activity attempts/completions.
"""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class RoutinedPlistEventData(events.EventData):
    """Apple iOS routined application plist event data.

    Attributes:
        key (str): The plist key associated with the event.
        value (str): The value associated with the key.
    """

    DATA_TYPE = 'ios:routined:entry'

    def __init__(self):
        """Initializes event data."""
        super(RoutinedPlistEventData, self).__init__(data_type=self.DATA_TYPE)
        self.key = None
        self.value = None


class RoutinedPlistPlugin(interface.PlistPlugin):
    """Plist parser plugin for Apple iOS routined application plist files."""

    NAME = 'ios_routined'
    DATA_FORMAT = 'Apple iOS routined application plist file'

    PLIST_PATH_FILTERS = frozenset([
        interface.PlistPathFilter('com.apple.routined.plist')
    ])

    def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
        """Extracts routined plist entries.

        Args:
            parser_mediator (ParserMediator): Mediates interactions between parsers
                and other components, such as storage and dfVFS.
            match (Optional[dict[str, object]]): Keys extracted from the plist file.
        """
        for key, value in match.items():
            try:
                event_data = RoutinedPlistEventData()
                event_data.key = key

                # Attempt to interpret ISO 8601 formatted strings as datetime values.
                event_data.value = dfdatetime_cocoa_time.CocoaTime(
                    timestamp=value)

                # Produce event data to be recorded by the parser mediator.
                parser_mediator.ProduceEventData(event_data)

            except ValueError:
                # Skip strings that cannot be interpreted as valid datetime values.
                continue


# Register the plugin with the PlistParser to make it available for plist parsing.
plist.PlistParser.RegisterPlugin(RoutinedPlistPlugin)
