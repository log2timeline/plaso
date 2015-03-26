# -*- coding: utf-8 -*-
"""Plugin for the Mac OS X launch services quarantine events."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class LsQuarantineEvent(time_events.CocoaTimeEvent):
  """Convenience class for a Mac OS X launch services quarantine event."""
  DATA_TYPE = 'macosx:lsquarantine'

  # TODO: describe more clearly what the data value contains.
  def __init__(self, cocoa_time, url, user_agent, data):
    """Initializes the event object.

    Args:
      cocoa_time: The Cocoa time value.
      url: The original URL of the file.
      user_agent: The user agent that was used to download the file.
      data: The data.
    """
    super(LsQuarantineEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.FILE_DOWNLOADED)

    self.url = url
    self.agent = user_agent
    self.data = data


class LsQuarantinePlugin(interface.SQLitePlugin):
  """Parses the launch services quarantine events database.

     The LS quarantine events are stored in SQLite database files named
     /Users/<username>/Library/Preferences/\
         QuarantineEvents.com.apple.LaunchServices
  """

  NAME = 'ls_quarantine'
  DESCRIPTION = u'Parser for LS quarantine events SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT LSQuarantineTimestamp AS Time, LSQuarantine'
        'AgentName AS Agent, LSQuarantineOriginURLString AS URL, '
        'LSQuarantineDataURLString AS Data FROM LSQuarantineEvent '
        'ORDER BY Time'), 'ParseLSQuarantineRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['LSQuarantineEvent'])

  def ParseLSQuarantineRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a launch services quarantine event row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    event_object = LsQuarantineEvent(
        row['Time'], row['URL'], row['Agent'], row['Data'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(LsQuarantinePlugin)
