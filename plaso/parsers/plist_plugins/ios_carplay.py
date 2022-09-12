# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS Car Play application plist files.

The plist contains history of opened applications in the Car Play application.
"""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSCarPlayHistoryEventData(events.EventData):
  """Apple iOS Car Play application history event data.

  Attributes:
    application_identifier (str): application identifier.
  """

  DATA_TYPE = 'ios:carplay:history:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSCarPlayHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application_identifier = None


class IOSCarPlayPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple iOS Car Play application plist files."""

  NAME = 'ios_carplay'
  DATA_FORMAT = 'Apple iOS Car Play application plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.CarPlayApp.plist')])

  PLIST_KEYS = frozenset(['CARRecentAppHistory'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract Car Play application history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    plist_key = match.get('CARRecentAppHistory', {})
    for application_identifier, datetime_value in plist_key.items():
      event_data = IOSCarPlayHistoryEventData()
      event_data.application_identifier = application_identifier

      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        timestamp = int(datetime_value * 1000000000)
        date_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
            timestamp=timestamp)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_USED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(IOSCarPlayPlistPlugin)
