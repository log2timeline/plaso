# -*- coding: utf-8 -*-
"""This file contains the ASL securityd log plaintext parser."""

import datetime
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

  DATA_TYPE = 'mac:asl:securityd:line'

  def __init__(
      self, timestamp, structure, sender, sender_pid,
      security_api, caller, message):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
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
        timestamp,
        eventdata.EventTimestamp.ADDED_TIME)
    self.timestamp = timestamp
    self.level = structure.level
    self.sender_pid = sender_pid
    self.facility = structure.facility
    self.sender = sender
    self.security_api = security_api
    self.caller = caller
    self.message = message


class MacSecuritydLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the securityd file that contains logs from the security daemon."""

  NAME = 'mac_securityd'
  DESCRIPTION = u'Parser for Mac OS X securityd log files.'

  ENCODING = u'utf-8'

  # Default ASL Securityd log.
  SECURITYD_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME.setResultsName('time') +
      pyparsing.CharsNotIn(u'[').setResultsName('sender') +
      pyparsing.Literal(u'[').suppress() +
      text_parser.PyparsingConstants.PID.setResultsName('sender_pid') +
      pyparsing.Literal(u']').suppress() +
      pyparsing.Literal(u'<').suppress() +
      pyparsing.CharsNotIn(u'>').setResultsName('level') +
      pyparsing.Literal(u'>').suppress() +
      pyparsing.Literal(u'[').suppress() +
      pyparsing.CharsNotIn(u'{').setResultsName('facility') +
      pyparsing.Literal(u'{').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(
          u'}').setResultsName('security_api')) +
      pyparsing.Literal(u'}').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(u']:').setResultsName('caller')) +
      pyparsing.Literal(u']:').suppress() +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('message'))

  # Repeated line.
  REPEATED_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME.setResultsName('time') +
      pyparsing.Literal(u'--- last message repeated').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('times') +
      pyparsing.Literal(u'time ---').suppress())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', SECURITYD_LINE),
      ('repeated', REPEATED_LINE)]

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
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """
    if key == 'repeated' or key == 'logline':
      return self._ParseLogLine(parser_mediator, structure, key)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a logline and store appropriate attributes.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """
    # TODO: improving this to get a valid year.
    if not self._year_use:
      self._year_use = parser_mediator.year

    if not self._year_use:
      # Get from the creation time of the file.
      self._year_use = self._GetYear(
          self.file_entry.GetStat(), parser_mediator.timezone)
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

    if key == 'logline':
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
      caller = 'unknown'
    if not structure.security_api:
      security_api = u'unknown'
    else:
      security_api = structure.security_api

    return MacSecuritydLogEvent(
        timestamp, structure, sender, structure.sender_pid, security_api,
        caller, message)

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

  def _GetYear(self, stat, zone):
    """Retrieves the year either from the input file or from the settings."""
    time = getattr(stat, 'crtime', 0)
    if not time:
      time = getattr(stat, 'ctime', 0)

    if not time:
      current_year = timelib.GetCurrentYear()
      logging.error((
          u'Unable to determine year of log file.\nDefaulting to: '
          u'{0:d}').format(current_year))
      return current_year

    try:
      timestamp = datetime.datetime.fromtimestamp(time, zone)
    except ValueError:
      current_year = timelib.GetCurrentYear()
      logging.error((
          u'Unable to determine year of log file.\nDefaulting to: '
          u'{0:d}').format(current_year))
      return current_year

    return timestamp.year


manager.ParsersManager.RegisterParser(MacSecuritydLogParser)
