# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

from __future__ import unicode_literals

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SafariHistoryEventData(events.EventData):
  """Safari history event data.

  Attributes:
    display_title (str): display title of the webpage visited.
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
    self.title = None
    self.url = None
    self.visit_count = None
    self.was_http_non_get = None


class SafariHistoryPlugin(interface.PlistPlugin):
  """Plugin to extract Safari history timestamps."""

  NAME = 'safari_history'
  DESCRIPTION = 'Parser for Safari history plist files.'

  PLIST_PATH = 'History.plist'
  PLIST_KEYS = frozenset(['WebHistoryDates', 'WebHistoryFileVersion'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts Safari history items.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    format_version = match.get('WebHistoryFileVersion', None)
    if format_version != 1:
      parser_mediator.ProduceExtractionWarning(
          'unsupported Safari history version: {0!s}'.format(format_version))
      return

    if 'WebHistoryDates' not in match:
      return

    for history_entry in match.get('WebHistoryDates', {}):
      last_visited_date = history_entry.get('lastVisitedDate', None)
      if last_visited_date is None:
        parser_mediator.ProduceExtractionWarning('missing last visited date')
        continue

      try:
        # Last visited date is a string containing a floating point value.
        timestamp = float(last_visited_date)
      except (TypeError, ValueError):
        parser_mediator.ProduceExtractionWarning(
            'unable to convert last visited date {0:s}'.format(
                last_visited_date))
        continue

      display_title = history_entry.get('displayTitle', None)

      event_data = SafariHistoryEventData()
      if display_title != event_data.title:
        event_data.display_title = display_title
      event_data.title = history_entry.get('title', None)
      event_data.url = history_entry.get('', None)
      event_data.visit_count = history_entry.get('visitCount', None)
      event_data.was_http_non_get = history_entry.get(
          'lastVisitWasHTTPNonGet', None)

      # Convert the floating point value to an integer.
      # TODO: add support for the fractional part of the floating point value.
      timestamp = int(timestamp)
      date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SafariHistoryPlugin)
