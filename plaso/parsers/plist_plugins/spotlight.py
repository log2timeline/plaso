# -*- coding: utf-8 -*-
"""Spotlight searched terms plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SpotlightPlugin(interface.PlistPlugin):
  """Basic plugin to extract information from Spotlight plist file.

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

  NAME = u'spotlight'
  DESCRIPTION = u'Parser for Spotlight plist files.'

  PLIST_PATH = u'com.apple.spotlight.plist'
  PLIST_KEYS = frozenset([u'UserShortcuts'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    shortcuts = match.get(u'UserShortcuts', {})
    for search_text, data in iter(shortcuts.items()):
      datetime_value = data.get(u'LAST_USED', None)
      if not datetime_value:
        continue

      display_name = data.get(u'DISPLAY_NAME', u'<DISPLAY_NAME>')
      path = data.get(u'PATH', u'<PATH>')

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          u'Spotlight term searched "{0:s}" associate to {1:s} ({2:s})').format(
              search_text, display_name, path)
      event_data.key = search_text
      event_data.root = u'/UserShortcuts'

      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightPlugin)
