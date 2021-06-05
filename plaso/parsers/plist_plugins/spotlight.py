# -*- coding: utf-8 -*-
"""Plist parser plugin for Spotlight searched terms plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightPlugin(interface.PlistPlugin):
  """Plist parser plugin for Spotlight searched terms plist files.

  Further information about extracted fields:
    name of the item:
      search term.

    PATH:
      path of the program associated to the term.

    LAST_USED:
      last time when it was executed.

    DISPLAY_NAME:
      the display name of the program associated.
  """

  NAME = 'spotlight'
  DATA_FORMAT = 'Spotlight plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.spotlight.plist')])

  PLIST_KEYS = frozenset(['UserShortcuts'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    shortcuts = match.get('UserShortcuts', {})
    for search_text, data in shortcuts.items():
      datetime_value = data.get('LAST_USED', None)
      if not datetime_value:
        continue

      display_name = data.get('DISPLAY_NAME', '<DISPLAY_NAME>')
      path = data.get('PATH', '<PATH>')

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          'Spotlight term searched "{0:s}" associate to {1:s} ({2:s})').format(
              search_text, display_name, path)
      event_data.key = search_text
      event_data.root = '/UserShortcuts'

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightPlugin)
