# -*- coding: utf-8 -*-
"""This file contains the wifi.log (Mac OS X) parser."""

import logging

import pyparsing

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class MacWifiLogEvent(time_events.TimestampEvent):
  """Convenience class for a Mac Wifi log line event."""

  DATA_TYPE = u'mac:wifilog:line'

  def __init__(self, timestamp, body):
    """Initializes the event object.

    Args:
      timestamp: the timestamp, contains the number of microseconds from
                 January 1, 1970 00:00:00 UTC.
      body: The body of the log message.
    """
    super(MacWifiLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.body = body

class MacWifiLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on wifi.log file."""

  NAME = u'macwifi'
  DESCRIPTION = u'Parser for Mac OS X wifi.log files.'

  _ENCODING = u'utf-8'


  # Define how a log line should look like.
  WIFI_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'body'))

  WIFI_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.Literal(u'***Starting Up***').setResultsName(u'text'))

  WIFI_TURNED_OVER_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      pyparsing.Combine(pyparsing.Word(pyparsing.printables) +
                        pyparsing.Word(pyparsing.printables) +
                        pyparsing.Literal(u'logfile turned over') +
                        pyparsing.LineEnd(), joinString=u' ', adjacent=False
                       ).setResultsName(u'body'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', WIFI_LINE),
      (u'header', WIFI_HEADER),
      (u'turned_over_header', WIFI_TURNED_OVER_HEADER)]

  def __init__(self):
    """Initializes a parser object."""
    super(MacWifiLogParser, self).__init__()
    self._last_month = None
    self._year_use = 0

  def _ConvertToTimestamp(self, day, month, year, time):
    """Converts date and time values into a timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37], 222]

    Args:
      day: an integer representing the day.
      month: an integer representing the month.
      year: an integer representing the year.
      time: a list containing integers with the number of
            hours, minutes and seconds.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.

    Raises:
      TimestampError: if the timestamp cannot be created from the date and
                      time values.
    """
    try:
      time_values, milliseconds = time
      hours, minutes, seconds = time_values
      microseconds = milliseconds * 1000
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hours, minutes, seconds, microseconds=microseconds)
    except ValueError:
      hours, minutes, seconds = time
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if not self._year_use:
      self._year_use = parser_mediator.GetEstimatedYear()

    # Gap detected between years.
    month = timelib.MONTH_DICT.get(structure.month.lower())
    if not self._last_month:
      self._last_month = month

    if month < self._last_month:
      self._year_use += 1

    try:
      timestamp = self._ConvertToTimestamp(
          structure.day, month, self._year_use, structure.time)
    except errors.TimestampError as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))
      return

    self._last_month = month

    body = structure.body

    event_object = MacWifiLogEvent(timestamp, body)
    parser_mediator.ProduceEvent(event_object)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key == u'logline' or key == u'header' or key == u'turned_over_header':
      self._ParseLogLine(parser_mediator, structure)
    else:
      logging.debug(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac Wifi log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      _ = self.WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      try:
        _ = self.WIFI_TURNED_OVER_HEADER.parseString(line)
      except pyparsing.ParseException:
        logging.debug(u'Not a Mac Wifi log file')
        return False
    return True


manager.ParsersManager.RegisterParser(MacWifiLogParser)
