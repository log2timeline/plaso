#-*- coding: utf-8 -*-
"""Text parser plugin for Android logcat files.

Android logcat can have a number of output forms, however this particular
parser only supports the 'threadtime' and 'time' formats.

In addition, support for the format modifiers:
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
    self.thread_identifier = None
    self.user_identifier = None


class AndroidLogcatTextPlugin(interface.TextPlugin):
  """Text parser plugin for Android logcat files."""

  NAME = 'android_logcat'
  DATA_FORMAT = 'Android logcat file'

  ENCODING = 'utf-8'

  _FULL_DATE_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2))

  _DATE_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2))

  _TIME_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, min=3, max=6))

  _TIME_ZONE = pyparsing.Combine(
      pyparsing.oneOf(['+', '-']) +
      pyparsing.Word(pyparsing.nums, exact=4))

  _PID_AND_THREAD_IDENTIFIER = (
      pyparsing.Word(pyparsing.nums).setResultsName('pid') +
      pyparsing.Word(pyparsing.nums).setResultsName('thread_identifier'))

  _USER_PID_AND_THREAD_IDENTIFIER = (
      pyparsing.Word(pyparsing.nums).setResultsName('user_identifier') +
      _PID_AND_THREAD_IDENTIFIER)

  _THREADTIME_LINE = (
      pyparsing.Or([_FULL_DATE_GROUP, _DATE_GROUP]).setResultsName('date') +
      _TIME_GROUP.setResultsName('time') +
      pyparsing.Optional(_TIME_ZONE).setResultsName('timezone') +
      pyparsing.Or([
          _USER_PID_AND_THREAD_IDENTIFIER, _PID_AND_THREAD_IDENTIFIER]) +
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Optional(pyparsing.Word(
          pyparsing.printables + ' ', excludeChars=':').setResultsName('tag')) +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine.setResultsName('message'))

  _TIME_LINE = (
      pyparsing.Or([_FULL_DATE_GROUP, _DATE_GROUP]).setResultsName('date') +
      _TIME_GROUP.setResultsName('time') +
      pyparsing.Optional(_TIME_ZONE).setResultsName('timezone') +
      pyparsing.Word('VDIWEFS', exact=1).setResultsName('priority') +
      pyparsing.Suppress('/') +
      pyparsing.Word(
          pyparsing.printables + ' ', excludeChars='(').setResultsName('tag') +
      pyparsing.Suppress('(') +
      pyparsing.Or([
          pyparsing.Word(pyparsing.nums).setResultsName('pid'),
          (pyparsing.Word(pyparsing.nums).setResultsName('user_identifier') +
           pyparsing.Suppress(':') +
           pyparsing.Word(pyparsing.nums).setResultsName('pid'))]) +
      pyparsing.Suppress(')') +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine.setResultsName('message'))

  _BEGINNING_LINE = (
      pyparsing.Suppress('--------- beginning of ') +
      pyparsing.oneOf(['events', 'kernel', 'main', 'radio', 'system']))

  _LINE_STRUCTURES = [
      ('beginning_line', _BEGINNING_LINE),
      ('threadtime_line', _THREADTIME_LINE),
      ('time_line', _TIME_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'beginning_line':
      return

    parsed_time = self._GetValueFromStructure(structure, 'time')
    parsed_date = self._GetValueFromStructure(structure, 'date')
    parsed_timezone = self._GetValueFromStructure(structure, 'timezone')
    if not parsed_timezone:
      timezone = parser_mediator.timezone
      parsed_timezone = datetime.datetime.now(timezone).strftime('%z')

    parsed_timezone = parsed_timezone[:3] + ':' + parsed_timezone[3:]

    if len(parsed_date) == 10:
      date_format = '{0:s}T{1:s}{2:s}'.format(
          parsed_date, parsed_time, parsed_timezone)
    else:
      estimated_year = parser_mediator.GetEstimatedYear()
      date_format = '{0:d}-{1:s}T{2:s}{3:s}'.format(
          estimated_year, parsed_date, parsed_time, parsed_timezone)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(date_format)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Invalid date time value with error: {0!s}'.format(exception))
      return

    component_tag = self._GetValueFromStructure(structure, 'tag')
    if component_tag:
      component_tag = component_tag.strip()

    event_data = AndroidLogcatEventData()
    event_data.file_offset = self._current_offset
    event_data.message = self._GetValueFromStructure(structure, 'message')
    event_data.pid = self._GetValueFromStructure(structure, 'pid')
    event_data.priority = self._GetValueFromStructure(structure, 'priority')
    event_data.component_tag = component_tag
    event_data.thread_identifier = self._GetValueFromStructure(
        structure, 'thread_identifier')
    event_data.user_identifier = self._GetValueFromStructure(
        structure, 'user_identifier')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    _, line_structure, parsed_structure = self._GetMatchingLineStructure(line)
    if not parsed_structure:
      return False

    if line_structure.name == 'beginning_line':
      return True

    return ('date' in parsed_structure and 'time' in parsed_structure and
            'message' in parsed_structure)


text_parser.SingleLineTextParser.RegisterPlugin(AndroidLogcatTextPlugin)
