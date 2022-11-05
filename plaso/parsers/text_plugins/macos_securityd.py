# -*- coding: utf-8 -*-
"""Text parser plugin for MacOS security daemon (securityd) log files.

Also see:
  https://opensource.apple.com/source/Security/Security-55471/sec/securityd
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSSecuritydLogEventData(events.EventData):
  """MacOS securityd log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    caller (str): caller, consists of two hex numbers.
    facility (str): facility.
    level (str): priority level.
    message (str): message.
    security_api (str): name of securityd function.
    sender (str): name of the sender.
    sender_pid (int): process identifier of the sender.
  """

  DATA_TYPE = 'macos:securityd_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSSecuritydLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.caller = None
    self.facility = None
    self.level = None
    self.message = None
    self.security_api = None
    self.sender = None
    self.sender_pid = None


class MacOSSecuritydLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for MacOS security daemon (securityd) log files."""

  NAME = 'mac_securityd'
  DATA_FORMAT = 'MacOS security daemon (securityd) log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _DATE_TIME = pyparsing.Group(
      _THREE_LETTERS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds'))

  _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).setParseAction(
      text_parser.PyParseIntCast)

  _SECURITYD_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.CharsNotIn('[').setResultsName('sender') +
      pyparsing.Literal('[').suppress() +
      _PROCESS_IDENTIFIER.setResultsName('sender_pid') +
      pyparsing.Literal(']').suppress() +
      pyparsing.Literal('<').suppress() +
      pyparsing.CharsNotIn('>').setResultsName('level') +
      pyparsing.Literal('>').suppress() +
      pyparsing.Literal('[').suppress() +
      pyparsing.CharsNotIn('{').setResultsName('facility') +
      pyparsing.Literal('{').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(
          '}').setResultsName('security_api')) +
      pyparsing.Literal('}').suppress() +
      pyparsing.Optional(pyparsing.CharsNotIn(']:').setResultsName(
          'caller')) + pyparsing.Literal(']:').suppress() +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('message'))

  _REPEATED_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('--- last message repeated').suppress() +
      _INTEGER.setResultsName('times') +
      pyparsing.Literal('time ---').suppress())

  _LINE_STRUCTURES = [
      ('logline', _SECURITYD_LINE),
      ('repeated', _REPEATED_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a text parser plugin."""
    super(MacOSSecuritydLogTextPlugin, self).__init__()
    self._repeated_structure = None

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    # If the actual entry is a repeated entry, we take the basic information
    # from the previous entry, but use the timestamp from the actual entry.
    if key == 'logline':
      self._repeated_structure = structure

      message = self._GetValueFromStructure(structure, 'message')
    else:
      repeat_count = self._GetValueFromStructure(structure, 'times')

      structure = self._repeated_structure

      message = self._GetValueFromStructure(
          structure, 'message', default_value='')
      message = 'Repeated {0:d} times: {1:s}'.format(repeat_count, message)

    caller = self._GetValueFromStructure(structure, 'caller', default_value='')
    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    caller = caller.strip()

    sender = self._GetValueFromStructure(structure, 'sender', default_value='')
    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    sender = sender.strip()

    event_data = MacOSSecuritydLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.caller = caller or None
    event_data.facility = self._GetValueFromStructure(structure, 'facility')
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.message = message
    event_data.security_api = self._GetValueFromStructure(
        structure, 'security_api')
    event_data.sender_pid = self._GetValueFromStructure(structure, 'sender_pid')
    event_data.sender = sender or None

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      month_string, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      month = self._GetMonthFromString(month_string)

      self._UpdateYear(month)

      relative_year = self._GetRelativeYear()

      time_elements_tuple = (
          relative_year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
          is_delta=True, time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

    try:
      parsed_structure = self._SECURITYD_LINE.parseString(line)
    except pyparsing.ParseException:
      parsed_structure = None

    if not parsed_structure:
      return False

    self._SetEstimatedYear(parser_mediator)

    time_elements_structure = self._GetValueFromStructure(
        parsed_structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._repeated_structure = None

    return True


text_parser.SingleLineTextParser.RegisterPlugin(MacOSSecuritydLogTextPlugin)
