# -*- coding: utf-8 -*-
"""Plist parser plugin for Car Play Application plist files.

It contains history of opened applications on Car Play Application.
"""

from dfdatetime import posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSCarPlayPlugin(interface.PlistPlugin):
  """Plist parser plugin for IOS Car Play Application plist files."""

  NAME = 'ios_carplay'
  DATA_FORMAT = 'iOS Car Play Application plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.CarPlayApp.plist')])

  PLIST_KEYS = frozenset(['CARRecentAppHistory'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract relevant Car Play Application entries."""
    recent_app_history = match.get('CARRecentAppHistory', {})
    for parameter, datetime_value in recent_app_history.items():
      event_data = plist_event.PlistTimeEventData()
      event_data.root = '/CARRecentAppHistory'

      if datetime_value:
        event_data.description = parameter
        event_data.key = parameter

        datetime_value = int(datetime_value)
        date_time = posix_time.PosixTime(timestamp=datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(IOSCarPlayPlugin)
