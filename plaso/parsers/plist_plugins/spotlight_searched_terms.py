# -*- coding: utf-8 -*-
"""Plist parser plugin for Spotlight searched terms plist files.

Fields within the plist key: com.apple.spotlight.plist, where the name of
the key contains the search term.
  DISPLAY_NAME: the display name of the program associated.
  LAST_USED: last time when it was executed.
  PATH: path of the program associated to the term.
"""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightSearchedTermsEventData(events.EventData):
  """Spotlight searched terms event data.

  Attributes:
    display_name (str): display name.
    last_used_time (dfdatetime.DateTimeValues): last date and time the search
        term was last used.
    path (str): path.
    search_term (str): search term.
  """

  DATA_TYPE = 'spotlight_searched_terms:entry'

  def __init__(self):
    """Initializes event data."""
    super(SpotlightSearchedTermsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.display_name = None
    self.last_used_time = None
    self.path = None
    self.search_term = None


class SpotlightSearchedTermsPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Spotlight searched terms plist files."""

  NAME = 'spotlight'
  DATA_FORMAT = 'Spotlight searched terms plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.spotlight.plist')])

  PLIST_KEYS = frozenset(['UserShortcuts'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    shortcuts = match.get('UserShortcuts', {})
    for search_term, plist_key in shortcuts.items():
      event_data = SpotlightSearchedTermsEventData()
      event_data.display_name = plist_key.get('DISPLAY_NAME', None)
      event_data.last_used_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LAST_USED')
      event_data.path = plist_key.get('PATH', None)
      event_data.search_term = search_term

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(SpotlightSearchedTermsPlistPlugin)
