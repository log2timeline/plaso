# -*- coding: utf-8 -*-
"""This file contains the ASL securityd log plaintext parser."""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# INFO:
# http://opensource.apple.com/source/Security/Security-55471/sec/securityd/


class MacSecuritydLogEvent(time_events.TimestampEvent):
  """Convenience class for a ASL securityd line event."""

  DATA_TYPE = u'mac:asl:securityd:line'

  def __init__(
      self, timestamp, structure, sender, sender_pid, security_api, caller,
      message):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      structure: Structure with the parse fields.
        level: String with the text representation of the priority level.
        facility: String with the ASL facility.
      sender: String with the name of the sender.
      sender_pid: Process id of the sender.
      security_api: Securityd function name.
      caller: The caller field, a string containing two hex numbers.
      message: String with the ASL message.
    """
    super(MacSecuritydLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.caller = caller
    self.facility = structure.facility
    self.level = structure.level
    self.message = message
    self.security_api = security_api
    self.sender_pid = sender_pid
    self.sender = sender


class MacSecuritydLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the securityd file that contains logs from the security daemon."""

  NAME = u'mac_securityd'
  DESCRIPTION = u'Parser for Mac OS X securityd log files.'

  _ENCODING = u'utf-8'

  # Default ASL Securityd log.
  SECURITYD_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      pyparsing.CharsNotIn(u'[').setResultsName(u'sender') +
      pyparsing.Literal(u'[').suppress() +
      text_parser.PyparsingConstants.PID.setResultsName(u'sender_pid') +
      pyparsing.Literal(u']').suppress() +
      pyparsing.Literal(u'<').suppress() +
      pyparsing.CharsNotIn(u'>').setResultsName(u'level') +
      pyparsing.Literal(u'>').suppress() +
      pyparsing.Literal(u'[').suppress() +
      pyparsing.CharsNotIn(u'{').setResultsName(u'facility') +
      pyparsing.Literal(u'{').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(
          u'}').setResultsName(u'security_api')) +
      pyparsing.Literal(u'}').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(u']:').setResultsName(
          u'caller')) + pyparsing.Literal(u']:').suppress() +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'message'))

  # Repeated line.
  REPEATED_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      pyparsing.Literal(u'--- last message repeated').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName(u'times') +
      pyparsing.Literal(u'time ---').suppress())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', SECURITYD_LINE),
      (u'repeated', REPEATED_LINE)]

  def __init__(self):
    """Initializes a parser object."""
    super(MacSecuritydLogParser, self).__init__()
    self._year_use = 0
    self._last_month = None
    self.previous_structure = None

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a ASL securityd log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      line = self.SECURITYD_LINE.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a ASL securityd log file')
      return False
    # Check if the day, month and time is valid taking a random year.
    month = timelib.MONTH_DICT.get(line.month.lower())
    if not month:
      return False
    if self._GetTimestamp(line.day, month, 2012, line.time) == 0:
      return False
    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key in [u'logline', u'repeated']:
      self._ParseLogLine(parser_mediator, structure, key)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    # TODO: improving this to get a valid year.
    if not self._year_use:
      self._year_use = parser_mediator.year

    if not self._year_use:
      # TODO: Find a decent way to actually calculate the correct year
      # instead of relying on stats object.
      self._year_use = parser_mediator.GetFileEntryYear()

      # If fail, get from the current time.
      if not self._year_use:
        self._year_use = timelib.GetCurrentYear()

    # Gap detected between years.
    month = timelib.MONTH_DICT.get(structure.month.lower())
    if not self._last_month:
      self._last_month = month
    if month < self._last_month:
      self._year_use += 1
    timestamp = self._GetTimestamp(
        structure.day,
        month,
        self._year_use,
        structure.time)
    if not timestamp:
      logging.debug(u'Invalid timestamp {0:s}'.format(structure.timestamp))
      return
    self._last_month = month

    if key == u'logline':
      self.previous_structure = structure
      message = structure.message
    else:
      times = structure.times
      structure = self.previous_structure
      message = u'Repeated {0:d} times: {1:s}'.format(
          times, structure.message)

    # It uses CarsNotIn structure which leaves whitespaces
    # at the beginning of the sender and the caller.
    sender = structure.sender.strip()
    caller = structure.caller.strip()
    if not caller:
      caller = u'unknown'
    if not structure.security_api:
      security_api = u'unknown'
    else:
      security_api = structure.security_api

    event_object = MacSecuritydLogEvent(
        timestamp, structure, sender, structure.sender_pid, security_api,
        caller, message)
    parser_mediator.ProduceEvent(event_object)

  def _GetTimestamp(self, day, month, year, time):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37]

    Args:
      day: An integer representing the day.
      month: An integer representing the month.
      year: An integer representing the year.
      time: A list containing the hours, minutes, seconds.

    Returns:
      timestamp: A plaso timestamp.
    """
    hours, minutes, seconds = time
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hours, minutes, seconds)


manager.ParsersManager.RegisterParser(MacSecuritydLogParser)
