# -*- coding: utf-8 -*-
"""Spotlight searched terms plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


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

  NAME = 'spotlight'
  DESCRIPTION = 'Parser for Spotlight plist files.'

  PLIST_PATH = 'com.apple.spotlight.plist'
  PLIST_KEYS = frozenset(['UserShortcuts'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    shortcuts = match.get('UserShortcuts', {})
    for search_text, data in iter(shortcuts.items()):
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

      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightPlugin)
