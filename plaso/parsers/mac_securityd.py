# -*- coding: utf-8 -*-
"""This file contains the Mac OS X securityd log plaintext parser.

Also see:
  http://opensource.apple.com/source/Security/Security-55471/sec/securityd/
"""

import logging

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacSecuritydLogEventData(events.EventData):
  """Mac OS X securityd log event data.

  Attributes:
    caller (str): caller, consists of two hex numbers.
    facility (str): facility.
    level (str): priority level.
    message (str): message.
    security_api (str): name of securityd function.
    sender_pid (int): process identifier of the sender.
    sender (str): name of the sender.
  """

  DATA_TYPE = u'mac:securityd:line'

  def __init__(self):
    """Initializes event data."""
    super(MacSecuritydLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller = None
    self.facility = None
    self.level = None
    self.message = None
    self.security_api = None
    self.sender = None
    self.sender_pid = None


class MacSecuritydLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the securityd file that contains logs from the security daemon."""

  NAME = u'mac_securityd'
  DESCRIPTION = u'Parser for Mac OS X securityd log files.'

  _ENCODING = u'utf-8'
  _DEFAULT_YEAR = 2012

  DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  SECURITYD_LINE = (
      DATE_TIME.setResultsName(u'date_time') +
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

  REPEATED_LINE = (
      DATE_TIME.setResultsName(u'date_time') +
      pyparsing.Literal(u'--- last message repeated').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName(u'times') +
      pyparsing.Literal(u'time ---').suppress())

  LINE_STRUCTURES = [
      (u'logline', SECURITYD_LINE),
      (u'repeated', REPEATED_LINE)]

  def __init__(self):
    """Initializes a parser object."""
    super(MacSecuritydLogParser, self).__init__()
    self._last_month = None
    self._previous_structure = None
    self._year_use = 0

  def _ConvertToTimestamp(self, day, month, year, time):
    """Converts date and time values into a timestamp.

    Args:
      day: an integer representing the day.
      month: an integer representing the month.
      year: an integer representing the year.
      time: a list containing integers with the number of
            hours, minutes and seconds.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.
    """
    hours, minutes, seconds = time
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hours, minutes, seconds)

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: contains:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
    """
    month, day, hours, minutes, seconds = structure.date_time

    # Note that dfdatetime_time_elements.TimeElements will raise ValueError
    # for an invalid month.
    month = timelib.MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._year_use += 1

    return (self._year_use, month, day, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetTimeElementsTuple(structure)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(structure.date_time))
      return

    self._last_month = time_elements_tuple[1]

    if key == u'logline':
      self._previous_structure = structure
      message = structure.message
    else:
      message = u'Repeated {0:d} times: {1:s}'.format(
          structure.times, self._previous_structure.message)
      structure = self._previous_structure

    # It uses CarsNotIn structure which leaves whitespaces
    # at the beginning of the sender and the caller.

    event_data = MacSecuritydLogEventData()
    event_data.caller = structure.caller.strip() or u'unknown'
    event_data.facility = structure.facility
    event_data.level = structure.level
    event_data.message = message
    event_data.security_api = structure.security_api or u'unknown'
    event_data.sender_pid = structure.sender_pid
    event_data.sender = structure.sender.strip()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in (u'logline', u'repeated'):
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseLogLine(parser_mediator, structure, key)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a securityd log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (bytes): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    self._last_month = 0
    self._year_use = parser_mediator.GetEstimatedYear()

    try:
      structure = self.SECURITYD_LINE.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a Mac securityd log file')
      return False

    time_elements_tuple = self._GetTimeElementsTuple(structure)

    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logging.debug(
          u'Not a Mac securityd log file, invalid date and time: {0!s}'.format(
              structure.date_time))
      return False

    self._last_month = time_elements_tuple[1]

    return True


manager.ParsersManager.RegisterParser(MacSecuritydLogParser)
