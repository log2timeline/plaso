# -*- coding: utf-8 -*-
"""Plist parser plugin for Safari history plist files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SafariHistoryEventData(events.EventData):
  """Safari history event data.

  Attributes:
    display_title (str): display title of the webpage visited.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    title (str): title of the webpage visited.
    url (str): URL visited.
    visit_count (int): number of times the website was visited.
    was_http_non_get (bool): True if the webpage was visited using a non-GET
        HTTP request.
  """

  DATA_TYPE = 'safari:history:visit'

  def __init__(self):
    """Initializes event data."""
    super(SafariHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.display_title = None
    self.last_visited_time = None
    self.title = None
    self.url = None
    self.visit_count = None
    self.was_http_non_get = None


class SafariHistoryPlugin(interface.PlistPlugin):
  """Plist parser plugin for Safari history plist files."""

  NAME = 'safari_history'
  DATA_FORMAT = 'Safari history plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('History.plist')])

  PLIST_KEYS = frozenset(['WebHistoryDates', 'WebHistoryFileVersion'])

  def _GetDateTimeValueFromTimestamp(
      self, parser_mediator, plist_key, plist_value_name):
    """Retrieves a date and time value from a Cocoa timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      plist_key (object): plist key.
      plist_value_name (str): name of the value in the plist key.

    Returns:
      dfdatetime.TimeElements: date and time or None if not available.
    """
    timestamp_string = plist_key.get(plist_value_name, None)
    if not timestamp_string:
      return None

    try:
      timestamp = float(timestamp_string)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning((
          'unable to convert Cocoa timestamp: {0:s} to a floating-point '
          'value').format(timestamp_string))
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts Safari history items.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    format_version = match.get('WebHistoryFileVersion', None)
    if format_version != 1:
      parser_mediator.ProduceExtractionWarning(
          'unsupported Safari history version: {0!s}'.format(format_version))
      return

    for history_entry in match.get('WebHistoryDates', {}):
      display_title = history_entry.get('displayTitle', None)
      title = history_entry.get('title', None)

      event_data = SafariHistoryEventData()
      event_data.last_visited_time = self._GetDateTimeValueFromTimestamp(
          parser_mediator, history_entry, 'lastVisitedDate')
      event_data.title = title
      event_data.url = history_entry.get('', None)
      event_data.visit_count = history_entry.get('visitCount', None)
      event_data.was_http_non_get = history_entry.get(
          'lastVisitWasHTTPNonGet', None)

      if display_title != title:
        event_data.display_title = display_title

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(SafariHistoryPlugin)
