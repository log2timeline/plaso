#-*- coding: utf-8 -*-
"""Text parser plugin for Android logcat files.

Android logcat can have a number of output formats. This parser supports:
* 'threadtime' format
* 'time' format

The log file format is:
date time PID-TID/package priority/tag: message

For example:
12-10 13:02:50.071 1901-4229/com.google.android.gms V/AuthZen: Handling
delegate intent.

Where priority is:
V: Verbose (lowest priority)
D: Debug
I: Info
W: Warning
E: Error
A: Assert

In addition, support for the format modifiers:
* date with a year
* user identifier (uid)
* microseconds fraction of second precision (usec)
* time zone offset

Also see:
  https://developer.android.com/studio/debug/logcat
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AndroidLogcatEventData(events.EventData):
  """Android logcat event data.

  Attributes:
    component_tag (str): the tag that indicates the system component from which
        the logcat line originates.
    file_offset (int): the file offset of where the log message was parsed.
    message (str): the log message.
    pid (int): process identifier (PID) that created the logcat line.
    priority (str): a character in the set {V, D, I, W, E, F, S}, which is
        ordered from lowest to highest priority.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    thread_identifier (int): thread identifier (TID) that created the logcat
        line.
    user_identifier (int): the user identifier (UID) or Android ID of
        the logged process.
  """

  DATA_TYPE = 'android:logcat'

  def __init__(self):
    """Initializes event data."""
    super(AndroidLogcatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.component_tag = None
    self.file_offset = None
    self.message = None
    self.pid = None
    self.priority = None
    self.recorded_time = None
    self.thread_identifier = None
    self.user_identifier = None


class AndroidLogcatTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for Android logcat files."""

  NAME = 'android_logcat'
  DATA_FORMAT = 'Android logcat file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _MONTH_DAY = (
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _YEAR_MONTH_DAY = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _FRACTION_OF_SECOND = (
      pyparsing.Word(pyparsing.nums, exact=3) ^
      pyparsing.Word(pyparsing.nums, exact=6))

  _DATE_TIME = (
      pyparsing.Or([_YEAR_MONTH_DAY, _MONTH_DAY]) +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _FRACTION_OF_SECOND)

  _TIME_ZONE_OFFSET = (
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  _PID_AND_THREAD_IDENTIFIER = (
      _INTEGER.setResultsName('pid') +
      _INTEGER.setResultsName('thread_identifier'))

  _USER_PID_AND_THREAD_IDENTIFIER = (
      _INTEGER.setResultsName('user_identifier') +
      _PID_AND_THREAD_IDENTIFIER)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _BEGINNING_LINE = (
      pyparsing.Suppress('--------- beginning of ') +
      pyparsing.oneOf(['events', 'kernel', 'main', 'radio', 'system']) +
      _END_OF_LINE)

  _THREADTIME_LINE_BODY = (
      pyparsing.Or([
          _USER_PID_AND_THREAD_IDENTIFIER, _PID_AND_THREAD_IDENTIFIER]) +
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Optional(pyparsing.Word(
          pyparsing.printables + ' ', excludeChars=':').setResultsName('tag')))

  _TIME_LINE_BODY = (
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Suppress('/') +
      pyparsing.Word(
          pyparsing.printables + ' ', excludeChars='(').setResultsName('tag') +
      pyparsing.Suppress('(') +
      pyparsing.Or([
          _INTEGER.setResultsName('pid'),
          (_INTEGER.setResultsName('user_identifier') +
           pyparsing.Suppress(':') + _INTEGER.setResultsName('pid'))]) +
      pyparsing.Suppress(')'))

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Optional(_TIME_ZONE_OFFSET).setResultsName('time_zone_offset') +
      (_THREADTIME_LINE_BODY ^ _TIME_LINE_BODY) +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine().setResultsName('message') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('beginning_line', _BEGINNING_LINE),
      ('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _BEGINNING_LINE ^ _LOG_LINE

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    if key != 'beginning_line':
      event_data = AndroidLogcatEventData()
      event_data.component_tag = self._GetStringValueFromStructure(
          structure, 'tag')
      event_data.file_offset = self._current_offset
      event_data.message = self._GetValueFromStructure(structure, 'message')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.priority = self._GetValueFromStructure(structure, 'priority')
      event_data.recorded_time = self._ParseTimeElements(structure)
      event_data.thread_identifier = self._GetValueFromStructure(
          structure, 'thread_identifier')
      event_data.user_identifier = self._GetValueFromStructure(
          structure, 'user_identifier')

      parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, structure):
    """Parses date and time elements of a log line.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      time_elements_structure = self._GetValueFromStructure(
          structure, 'date_time')

      has_year = len(time_elements_structure) == 7

      if has_year:
        (year, month, day_of_month, hours, minutes, seconds,
         fraction_of_second_string) = time_elements_structure
      else:
        (month, day_of_month, hours, minutes, seconds,
         fraction_of_second_string) = time_elements_structure

        self._UpdateYear(month)

        year = self._GetRelativeYear()

      time_zone_offset = self._GetValueFromStructure(
          structure, 'time_zone_offset')
      if time_zone_offset:
        time_zone_sign, time_zone_hours, time_zone_minutes = time_zone_offset

        time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
        if time_zone_sign == '-':
          time_zone_offset *= -1

      fraction_of_second = int(fraction_of_second_string, 10)

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds,
          fraction_of_second)

      if len(fraction_of_second_string) == 3:
        date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
            is_delta=(not has_year), time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)
      else:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
            is_delta=(not has_year), time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)

      if time_zone_offset is None:
        date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._SetEstimatedYear(parser_mediator)

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')
    if time_elements_structure:
      try:
        self._ParseTimeElements(time_elements_structure)
      except errors.ParseError:
        return False

    return True


text_parser.TextLogParser.RegisterPlugin(AndroidLogcatTextPlugin)
