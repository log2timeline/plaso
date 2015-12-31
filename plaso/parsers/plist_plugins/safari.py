# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

import logging

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SafariHistoryEvent(time_events.TimestampEvent):
  """An EventObject for Safari history entries."""

  DATA_TYPE = u'safari:history:visit'

  def __init__(self, timestamp, history_entry):
    """Initialize the event.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      history_entry: A dict object read from the Safari history plist.
    """
    super(SafariHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.LAST_VISITED_TIME)
    self.url = history_entry.get(u'', None)
    self.title = history_entry.get(u'title', None)
    display_title = history_entry.get(u'displayTitle', None)
    if display_title != self.title:
      self.display_title = display_title
    self.visit_count = history_entry.get(u'visitCount', None)
    self.was_http_non_get = history_entry.get(u'lastVisitWasHTTPNonGet', None)


class SafariHistoryPlugin(interface.PlistPlugin):
  """Plugin to extract Safari history timestamps."""

  NAME = u'safari_history'
  DESCRIPTION = u'Parser for Safari history plist files.'

  PLIST_PATH = u'History.plist'
  PLIST_KEYS = frozenset([u'WebHistoryDates', u'WebHistoryFileVersion'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts Safari history items.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    if match.get(u'WebHistoryFileVersion', 0) != 1:
      logging.warning(u'Unable to parse Safari version: {0:s}'.format(
          match.get(u'WebHistoryFileVersion', 0)))
      return

    if u'WebHistoryDates' not in match:
      return

    for history_entry in match.get(u'WebHistoryDates', {}):
      try:
        time = timelib.Timestamp.FromCocoaTime(float(
            history_entry.get(u'lastVisitedDate', 0)))
      except ValueError:
        logging.warning(u'Unable to translate timestamp: {0:s}'.format(
            history_entry.get(u'lastVisitedDate', 0)))
        continue

      if not time:
        logging.debug(u'No timestamp set, skipping record.')
        continue

      event_object = SafariHistoryEvent(time, history_entry)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(SafariHistoryPlugin)
