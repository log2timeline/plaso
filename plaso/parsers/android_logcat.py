#-*- coding: utf-8 -*-
"""This file contains a parser for Android logcat output.

Android logcat can have a number of output forms, however this particular
parser only supports the 'threadtime' and 'time' formats.

In addition, support for the format modifiers
- uid
- usec
- UTC | zone
- year
"""
import datetime

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


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
    tid (int): thread identifier (TID) that created the logcat line.
    uid (int): the UID or Android ID of the logged process.
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
    self.tid = None
    self.uid = None


class AndroidLogcatParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for Android logcat output."""

  NAME = 'android_logcat'
  DATA_FORMAT = 'Android Logcat output'

  _ENCODING = 'utf-8'

  _ANDROID_FULL_DATE_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2))

  _ANDROID_DATE_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2))

  _ANDROID_TIME_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, min=3, max=6))

  _ANDROID_TIME_ZONE = pyparsing.Combine(
      pyparsing.oneOf(['+','-']) +
      pyparsing.Word(pyparsing.nums, exact=4))

  _ANDROID_THREADTIME_LINE = (
      pyparsing.Or([
          _ANDROID_FULL_DATE_GROUP,
          _ANDROID_DATE_GROUP]).setResultsName('date') +
      _ANDROID_TIME_GROUP.setResultsName('time') +
      pyparsing.Optional(_ANDROID_TIME_ZONE).setResultsName('timezone') +
      pyparsing.Or([
          (pyparsing.Word(pyparsing.nums).setResultsName('uid') +
           pyparsing.Word(pyparsing.nums).setResultsName('pid') +
           pyparsing.Word(pyparsing.nums).setResultsName('tid')),
          (pyparsing.Word(pyparsing.nums).setResultsName('pid') +
           pyparsing.Word(pyparsing.nums).setResultsName('tid'))]) +
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Optional(pyparsing.Word(
          pyparsing.printables + ' ',
          exclude_chars=':').setResultsName('tag')) +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine.setResultsName('message'))

  _ANDROID_TIME_LINE = (
      pyparsing.Or([
          _ANDROID_FULL_DATE_GROUP,
          _ANDROID_DATE_GROUP]).setResultsName('date') +
      _ANDROID_TIME_GROUP.setResultsName('time') +
      pyparsing.Optional(_ANDROID_TIME_ZONE).setResultsName('timezone') +
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Suppress('/') +
      pyparsing.Word(
          pyparsing.printables + ' ',
          exclude_chars='(').setResultsName('tag') +
      pyparsing.Suppress('(') +
      pyparsing.Or([
          pyparsing.Word(pyparsing.nums).setResultsName('pid'),
          (pyparsing.Word(pyparsing.nums).setResultsName('uid') +
           pyparsing.Suppress(':') +
           pyparsing.Word(pyparsing.nums).setResultsName('pid'))]) +
      pyparsing.Suppress(')') +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine.setResultsName('message'))

  _BEGINNING_LINE = (
      pyparsing.Suppress('--------- beginning of ') +
      pyparsing.oneOf(['events', 'kernel', 'main', 'radio', 'system']))

  LINE_STRUCTURES = [
      ('beginning_line', _BEGINNING_LINE),
      ('threadtime_line', _ANDROID_THREADTIME_LINE),
      ('time_line', _ANDROID_TIME_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'beginning_line':
      return

    if key in ('threadtime_line', 'time_line'):
      parsed_time = self._GetValueFromStructure(structure, 'time')
      parsed_date = self._GetValueFromStructure(structure, 'date')
      parsed_timezone = self._GetValueFromStructure(structure, 'timezone')
      if not parsed_timezone:
        timezone = parser_mediator.timezone
        parsed_timezone = datetime.datetime.now(timezone).strftime('%z')

      parsed_timezone = parsed_timezone[:3] + ':' + parsed_timezone[3:]

      if len(parsed_date) == 10:
        date_format = f'{parsed_date}T{parsed_time}{parsed_timezone}'
      else:
        estimated_year = parser_mediator.GetEstimatedYear()
        date_format = (f'{estimated_year}-{parsed_date}T'
                       f'{parsed_time}{parsed_timezone}')

      new_date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

      try:
        new_date_time.CopyFromStringISO8601(date_format)
      except ValueError as error:
        parser_mediator.ProduceExtractionWarning(
            'Invalid date time value: {0:s}'.format(error))
        return

      event_data = AndroidLogcatEventData()
      event_data.file_offset = self._current_offset
      event_data.message = self._GetValueFromStructure(structure, 'message')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.priority = self._GetValueFromStructure(structure, 'priority')
      event_data.component_tag = self._GetValueFromStructure(structure, 'tag')
      if event_data.component_tag:
        event_data.component_tag = event_data.component_tag.strip()
      event_data.tid = self._GetValueFromStructure(structure, 'tid')
      event_data.uid = self._GetValueFromStructure(structure, 'uid')

      event = time_events.DateTimeValuesEvent(
          new_date_time, definitions.TIME_DESCRIPTION_RECORDED)

      parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    for format_name, line_format in self.LINE_STRUCTURES:
      try:
        structure = line_format.parseString(line)

      except pyparsing.ParseException:
        logger.debug('Not a Android logcat format')
        continue

      if format_name == 'beginning_line':
        return True

      if 'date' in structure and 'time' in structure and 'message' in structure:
        return True

    return False


manager.ParsersManager.RegisterParser(AndroidLogcatParser)
