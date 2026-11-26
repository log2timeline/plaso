"""Default plist parser plugin."""

import datetime

import pytz

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
    """Default plist parser plugin."""

    NAME = "plist_default"
    DATA_FORMAT = "plist file"

    # pylint: disable=arguments-differ
    def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
        """Extracts events from the values of entries within a plist.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          top_level (Optional[dict[str, object]]): plist top-level item.
        """
        for root, key_name, datetime_value in self._RecurseKey(top_level):
            if not isinstance(datetime_value, datetime.datetime):
                continue

            # plistlib returns naive date and time values that represent UTC.
            # Convert aware values to UTC instead of overwriting their time zone.
            if datetime_value.tzinfo is None:
                datetime_value = datetime_value.replace(tzinfo=pytz.UTC)
            else:
                datetime_value = datetime_value.astimezone(pytz.UTC)

            date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
            date_time.CopyFromDatetime(datetime_value)

            event_data = plist_event.PlistTimeEventData()
            event_data.key = key_name
            event_data.root = root
            event_data.written_time = date_time

            parser_mediator.ProduceEventData(event_data)

            # TODO: adjust code when there is a way to map keys to offsets.


plist.PlistParser.RegisterPlugin(DefaultPlugin)
