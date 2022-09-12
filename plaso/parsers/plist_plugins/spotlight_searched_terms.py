# -*- coding: utf-8 -*-
"""Plist parser plugin for Spotlight searched terms plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightSearchedTermsEventData(events.EventData):
  """Spotlight searched terms event data.

  Attributes:
    display_name (str): display name.
    path (str): path.
    search_term (str): search term.
  """

  DATA_TYPE = 'spotlight_searched_terms:entry'

  def __init__(self):
    """Initializes event data."""
    super(SpotlightSearchedTermsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.display_name = None
    self.path = None
    self.search_term = None


class SpotlightSearchedTermsPlistPlugin(interface.PlistPlugin):
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
    for search_term, data in shortcuts.items():
      event_data = SpotlightSearchedTermsEventData()
      event_data.display_name = data.get('DISPLAY_NAME', None)
      event_data.path = data.get('PATH', None)
      event_data.search_term = search_term

      datetime_value = data.get('LAST_USED', None)
      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_USED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightSearchedTermsPlistPlugin)
