# -*- coding: utf-8 -*-
"""This file contains a Symantec parser in plaso."""

from plaso.events import text_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser

import pytz


__author__ = 'David Nides (david.nides@gmail.com)'


class SymantecEvent(text_events.TextEvent):
  """Convenience class for a Symantec line event."""
  DATA_TYPE = u'av:symantec:scanlog'


class SymantecParser(text_parser.TextCSVParser):
  """Parse Symantec AV Corporate Edition and Endpoint Protection log files."""

  NAME = u'symantec_scanlog'
  DESCRIPTION = u'Parser for Symantec Anti-Virus log files.'

  # Define the columns that make up the structure of a Symantec log file.
  # http://www.symantec.com/docs/TECH100099
  COLUMNS = [
      u'time', u'event', u'cat', u'logger', u'computer', u'user',
      u'virus', u'file', u'action1', u'action2', u'action0', u'virustype',
      u'flags', u'description', u'scanid', u'new_ext', u'groupid',
      u'event_data', u'vbin_id', u'virus_id', u'quarfwd_status',
      u'access', u'snd_status', u'compressed', u'depth', u'still_infected',
      u'definfo', u'defseqnumber', u'cleaninfo', u'deleteinfo',
      u'backup_id', u'parent', u'guid', u'clientgroup', u'address',
      u'domainname', u'ntdomain', u'macaddr', u'version:',
      u'remote_machine', u'remote_machine_ip', u'action1_status',
      u'action2_status', u'license_feature_name', u'license_feature_ver',
      u'license_serial_num', u'license_fulfillment_id', u'license_start_dt',
      u'license_expiration_dt', u'license_lifecycle', u'license_seats_total',
      u'license_seats', u'err_code', u'license_seats_delta', u'status',
      u'domain_guid', u'log_session_guid', u'vbin_session_id',
      u'login_domain', u'extra']

  def _ConvertToTimestamp(self, date_time_values, timezone=pytz.UTC):
    """Converts the given parsed date and time values to a timestamp.

    The date and time values consist of six hexadecimal octets.
    They represent the following:
      First octet: Number of years since 1970
      Second octet: Month, where January = 0
      Third octet: Day
      Fourth octet: Hour
      Fifth octet: Minute
      Sixth octet: Second

    For example, 200A13080122 represents November 19, 2002, 8:01:34 AM.

    Args:
      date_time_values: The hexadecimal encoded date and time values.
      timezone: Optional timezone (instance of pytz.timezone).

    Returns:
      A timestamp value, contains the number of micro seconds since
      January 1, 1970, 00:00:00 UTC.
    """
    if not date_time_values:
      return timelib.Timestamp.NONE_TIMESTAMP

    year, month, day, hours, minutes, seconds = (
        int(hexdigit[0] + hexdigit[1], 16) for hexdigit in zip(
            date_time_values[::2], date_time_values[1::2]))

    return timelib.Timestamp.FromTimeParts(
        year + 1970, month + 1, day, hours, minutes, seconds, timezone=timezone)

  def VerifyRow(self, parser_mediator, row):
    """Verify a single line of a Symantec log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: A single row from the CSV file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      timestamp = self._ConvertToTimestamp(
          row[u'time'], timezone=parser_mediator.timezone)
    except (TypeError, ValueError, errors.TimestampError):
      return False

    if not timestamp:
      return False

    # Check few entries.
    try:
      my_event = int(row[u'event'])
    except (TypeError, ValueError):
      return False

    if my_event < 1 or my_event > 77:
      return False

    try:
      category = int(row[u'cat'])
    except (TypeError, ValueError):
      return False

    if category < 1 or category > 4:
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
    try:
      timestamp = self._ConvertToTimestamp(
          row[u'time'], timezone=parser_mediator.timezone)
    except (TypeError, ValueError, errors.TimestampError) as exception:
      timestamp = timelib.Timestamp.NONE_TIMESTAMP
      parser_mediator.ProduceParseError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))

    # TODO: Create new dict object that only contains valuable attributes.
    event_object = SymantecEvent(timestamp, row_offset, row)
    parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(SymantecParser)
