# -*- coding: utf-8 -*-
"""Parser for McAfee Anti-Virus Logs.

McAfee AV uses 4 logs to track when scans were run, when virus databases were
updated, and when files match the virus database."""

import logging

from plaso.events import text_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class McafeeAVEvent(text_events.TextEvent):
  """Convenience class for McAfee AV Log events """
  DATA_TYPE = u'av:mcafee:accessprotectionlog'

  def __init__(self, timestamp, offset, attributes):
    """Initializes a McAfee AV Log Event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the attributes.
      attributes: Dict of elements from the AV log line.
    """
    del attributes[u'time']
    del attributes[u'date']
    super(McafeeAVEvent, self).__init__(timestamp, offset, attributes)
    self.full_path = attributes[u'filename']


class McafeeAccessProtectionParser(text_parser.TextCSVParser):
  """Parses the McAfee AV Access Protection Log."""

  NAME = u'mcafee_protection'
  DESCRIPTION = u'Parser for McAfee AV Access Protection log files.'

  VALUE_SEPARATOR = b'\t'
  # Define the columns of the McAfee AV Access Protection Log.
  COLUMNS = [u'date', u'time', u'status', u'username', u'filename',
             u'trigger_location', u'rule', u'action']

  def _GetTimestamp(self, parser_mediator, date, time):
    """Determines a timestamp from the time string.

    The date and time are made up of two strings, the date and the time,
    separated by a tab. The time is in local time. The month and day can
    be either 1 or 2 characters long, e.g.: 7/30/2013\\t10:22:48 AM

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      date: The string representing the date.
      time: The string representing the time.

    Returns:
      The timestamp time value. The timestamp contains the number of
      microseconds since Jan 1, 1970 00:00:00 UTC or None if the time string
      could not be parsed.
    """
    # TODO: check if this is correct, likely not date or not time
    # is more accurate.
    if not (date and time):
      logging.warning(u'Unable to extract timestamp from McAfee AV logline.')
      return

    # TODO: Figure out how McAfee sets Day First and use that here.
    # The in-file time format is '07/30/2013\t10:22:48 AM'.
    time_string = u'{0:s} {1:s}'.format(date, time)
    try:
      return timelib.Timestamp.FromTimeString(
          time_string, timezone=parser_mediator.timezone)

    except errors.TimestampError:
      parser_mediator.ProduceParseError(
          u'Unable to parse time string: {0:s}'.format(time_string))

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
    if row[u'date'][0:3] == b'\xef\xbb\xbf':
      row[u'date'] = row[u'date'][3:]
      self.encoding = u'utf-8'

    # Check the date format!
    # If it doesn't pass, then this isn't a McAfee AV Access Protection Log
    timestamp = self._GetTimestamp(parser_mediator, row[u'date'], row[u'time'])
    if timestamp is None:
      return False

    # Use the presence of these strings as a backup or in case of partial file.
    if (not u'Access Protection' in row[u'status'] and
        not u'Would be blocked' in row[u'status']):
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
    timestamp = self._GetTimestamp(parser_mediator, row[u'date'], row[u'time'])
    if timestamp is not None:
      event_object = McafeeAVEvent(timestamp, row_offset, row)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(McafeeAccessProtectionParser)
