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

  def __init__(self, timestamp, history_entry):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the Event, in microseconds since Unix Epoch.
      history_entry: A dict object read from the Safari history plist.
    """
    super(SafariHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.LAST_VISITED_TIME)
    self.data_type = 'safari:history:visit'
    self.url = history_entry.get('', None)
    self.title = history_entry.get('title', None)
    display_title = history_entry.get('displayTitle', None)
    if display_title != self.title:
      self.display_title = display_title
    self.visit_count = history_entry.get('visitCount', None)
    self.was_http_non_get = history_entry.get('lastVisitWasHTTPNonGet', None)


class SafariHistoryPlugin(interface.PlistPlugin):
  """Plugin to extract Safari history timestamps."""

  NAME = 'safari_history'
  DESCRIPTION = u'Parser for Safari history plist files.'

  PLIST_PATH = 'History.plist'
  PLIST_KEYS = frozenset(['WebHistoryDates', 'WebHistoryFileVersion'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts Safari history items.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    if match.get('WebHistoryFileVersion', 0) != 1:
      logging.warning(u'Unable to parse Safari version: {0:s}'.format(
          match.get('WebHistoryFileVersion', 0)))
      return

    for history_entry in match.get('WebHistoryDates', {}):
      try:
        time = timelib.Timestamp.FromCocoaTime(float(
            history_entry.get('lastVisitedDate', 0)))
      except ValueError:
        logging.warning(u'Unable to translate timestamp: {0:s}'.format(
            history_entry.get('lastVisitedDate', 0)))
        continue

      if not time:
        logging.debug('No timestamp set, skipping record.')
        continue

      event_object = SafariHistoryEvent(time, history_entry)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(SafariHistoryPlugin)
