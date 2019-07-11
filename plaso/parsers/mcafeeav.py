# -*- coding: utf-8 -*-
"""Parser for McAfee Anti-Virus Logs.

McAfee AV uses 4 logs to track when scans were run, when virus databases were
updated, and when files match the virus database."""

from __future__ import unicode_literals

import codecs

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class McafeeAVEventData(events.EventData):
  """McAfee AV Log event data.

  Attributes:
    action (str): action.
    filename (str): filename.
    rule (str): rule.
    status (str): status.
    trigger_location (str): trigger location.
    username (str): username.
  """

  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  def __init__(self):
    """Initializes event data."""
    super(McafeeAVEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.filename = None
    self.rule = None
    self.status = None
    self.trigger_location = None
    self.username = None


class McafeeAccessProtectionParser(dsv_parser.DSVParser):
  """Parses the McAfee AV Access Protection Log."""

  NAME = 'mcafee_protection'
  DESCRIPTION = 'Parser for McAfee AV Access Protection log files.'

  DELIMITER = b'\t'
  COLUMNS = [
      'date', 'time', 'status', 'username', 'filename',
      'trigger_location', 'rule', 'action']

  def _ConvertToTimestamp(self, date, time, timezone):
    """Converts date and time values into a timestamp.

    The date and time are made up of two strings, the date and the time,
    separated by a tab. The time is in local time. The month and day can
    be either 1 or 2 characters long, for example: "7/30/2013\\t10:22:48 AM"

    Args:
      date (str): date.
      time (str): time.
      timezone (pytz.timezone): timezone of the date and time.

    Returns:
      int: a timestamp integer containing the number of micro seconds since
          January 1, 1970, 00:00:00 UTC.

    Raises:
      TimestampError: if the timestamp is badly formed or unable to transfer
          the supplied date and time into a timestamp.
    """
    # TODO: check if this is correct, likely not date or not time
    # is more accurate.
    if not date and not time:
      raise errors.TimestampError(
          'Unable to extract timestamp from McAfee AV logline.')

    # TODO: Figure out how McAfee sets Day First and use that here.
    # The in-file time format is '07/30/2013\t10:22:48 AM'.
    try:
      time_string = '{0:s} {1:s}'.format(date, time)
    except UnicodeDecodeError:
      raise errors.TimestampError('Unable to form a timestamp string.')

    return timelib.Timestamp.FromTimeString(time_string, timezone=timezone)

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    try:
      timestamp = self._ConvertToTimestamp(
          row['date'], row['time'], parser_mediator.timezone)
    except errors.TimestampError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse time string: [{0:s} {1:s}] with error {2:s}'.format(
              repr(row['date']), repr(row['time']), exception))
      return

    if timestamp is None:
      return

    event_data = McafeeAVEventData()
    event_data.action = row['action']
    event_data.filename = row['filename']
    event_data.offset = row_offset
    event_data.rule = row['rule']
    event_data.status = row['status']
    event_data.trigger_location = row['trigger_location']
    event_data.username = row['username']

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) != 8:
      return False

    # This file can have a UTF-8 byte-order-marker at the beginning of
    # the first row.
    # TODO: Find out all the code pages this can have.  Asked McAfee 10/31.
    row_bytes = codecs.encode(row['date'], parser_mediator.codepage)
    if row_bytes.startswith(b'\xef\xbb\xbf'):
      row['date'] = row['date'][3:]
      self._encoding = 'utf-8'

    # Check the date format!
    # If it doesn't parse, then this isn't a McAfee AV Access Protection Log
    try:
      timestamp = self._ConvertToTimestamp(
          row['date'], row['time'], parser_mediator.timezone)
    except errors.TimestampError:
      return False

    if timestamp is None:
      return False

    # Use the presence of these strings as a backup or in case of partial file.
    if (not 'Access Protection' in row['status'] and
        not 'Would be blocked' in row['status']):
      return False

    return True


manager.ParsersManager.RegisterParser(McafeeAccessProtectionParser)
