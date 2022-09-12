# -*- coding: utf-8 -*-
"""Plist parser plugin for iOS Car Play Application plist files.

The plist contains history of opened applications in the Car Play Application.
"""

from dfdatetime import posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSCarPlayPlugin(interface.PlistPlugin):
  """Plist parser plugin for iOS Car Play Application plist files."""

  NAME = 'ios_carplay'
  DATA_FORMAT = 'iOS Car Play Application plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.CarPlayApp.plist')])

  PLIST_KEYS = frozenset(['CARRecentAppHistory'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract Car Play Application history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    event_data = plist_event.PlistTimeEventData()
    event_data.root = '/CARRecentAppHistory'

    plist_key = match.get('CARRecentAppHistory', {})
    for parameter, datetime_value in plist_key.items():
      event_data.desc = parameter
      event_data.key = parameter

      if datetime_value:
        timestamp = int(datetime_value * 1000000000)
        date_time = posix_time.PosixTimeInNanoseconds(timestamp=timestamp)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(IOSCarPlayPlugin)
