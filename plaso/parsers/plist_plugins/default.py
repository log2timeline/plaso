# -*- coding: utf-8 -*-
"""Default plist parser plugin."""

import datetime

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
  """Default plist parser plugin."""

  NAME = 'plist_default'
  DATA_FORMAT = 'plist file'

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts events from the values of entries within a plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for root, key, datetime_value in self._RecurseKey(top_level):
      if not isinstance(datetime_value, datetime.datetime):
        continue

      event_data = plist_event.PlistTimeEventData()
      event_data.key = key
      event_data.root = root

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      # TODO: adjust code when there is a way to map keys to offsets.


plist.PlistParser.RegisterPlugin(DefaultPlugin)
