# -*- coding: utf-8 -*-
"""This file contains the Spotlight searched terms plugin in Plaso."""

from plaso.containers import plist_event
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
      if not u'LAST_USED' in data:
        continue
      description = (
          u'Spotlight term searched "{0:s}" associate to {1:s} '
          u'({2:s})').format(
              search_text, data.get(u'DISPLAY_NAME', u'<DISPLAY_NAME>'),
              data.get(u'PATH', u'<PATH>'))
      event_object = plist_event.PlistEvent(
          u'/UserShortcuts', search_text, data[u'LAST_USED'], description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(SpotlightPlugin)
