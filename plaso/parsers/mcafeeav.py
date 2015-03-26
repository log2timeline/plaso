# -*- coding: utf-8 -*-
"""Parser for McAfee Anti-Virus Logs.

McAfee AV uses 4 logs to track when scans were run, when virus databases were
updated, and when files match the virus database."""

import logging

from plaso.events import text_events
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class McafeeAVEvent(text_events.TextEvent):
  """Convenience class for McAfee AV Log events """
  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  def __init__(self, timestamp, offset, attributes):
    """Initializes a McAfee AV Log Event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the attributes.
      attributes: Dict of elements from the AV log line.
    """
    del attributes['time']
    del attributes['date']
    super(McafeeAVEvent, self).__init__(timestamp, offset, attributes)
    self.full_path = attributes['filename']


class McafeeAccessProtectionParser(text_parser.TextCSVParser):
  """Parses the McAfee AV Access Protection Log."""

  NAME = 'mcafee_protection'
  DESCRIPTION = u'Parser for McAfee AV Access Protection log files.'

  VALUE_SEPARATOR = '\t'
  # Define the columns of the McAfee AV Access Protection Log.
  COLUMNS = ['date', 'time', 'status', 'username', 'filename',
             'trigger_location', 'rule', 'action']

  def _GetTimestamp(self, date, time, timezone):
    """Return a 64-bit signed timestamp in microseconds since Epoch.

     The timestamp is made up of two strings, the date and the time, separated
     by a tab. The time is in local time. The month and day can be either 1 or 2
     characters long.  E.g.: 7/30/2013\t10:22:48 AM

     Args:
       date: The string representing the date.
       time: The string representing the time.
       timezone: The timezone object.

     Returns:
       A plaso timestamp value, microseconds since Epoch in UTC or None.
    """

    if not (date and time):
      logging.warning('Unable to extract timestamp from McAfee AV logline.')
      return

    # TODO: Figure out how McAfee sets Day First and use that here.
    # The in-file time format is '07/30/2013\t10:22:48 AM'.
    return timelib.Timestamp.FromTimeString(
        u'{0:s} {1:s}'.format(date, time), timezone=timezone)

  def VerifyRow(self, parser_mediator, row):
    """Verify that this is a McAfee AV Access Protection Log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: A single row from the CSV file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    if len(row) != 8:
      return False

    # This file can have a UTF-8 byte-order-marker at the beginning of
    # the first row.
    # TODO: Find out all the code pages this can have.  Asked McAfee 10/31.
    if row['date'][0:3] == '\xef\xbb\xbf':
      row['date'] = row['date'][3:]

    # Check the date format!
    # If it doesn't pass, then this isn't a McAfee AV Access Protection Log
    try:
      self._GetTimestamp(row['date'], row['time'], parser_mediator.timezone)
    except (TypeError, ValueError):
      return False

    # Use the presence of these strings as a backup or in case of partial file.
    if (not 'Access Protection' in row['status'] and
        not 'Would be blocked' in row['status']):
      return False

    return True

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a row and extract event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row_offset: The offset of the row.
      row: A dictionary containing all the fields as denoted in the
           COLUMNS class list.
    """
    timestamp = self._GetTimestamp(
        row['date'], row['time'], parser_mediator.timezone)
    event_object = McafeeAVEvent(timestamp, row_offset, row)
    parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(McafeeAccessProtectionParser)
