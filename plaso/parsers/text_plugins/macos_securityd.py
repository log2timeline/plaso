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
      lambda tokens: int(tokens[0], 10))

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _DATE_TIME = pyparsing.Group(
      _THREE_LETTERS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds'))

  _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.CharsNotIn('[').setResultsName('sender') +
      pyparsing.Suppress('[') +
      _PROCESS_IDENTIFIER.setResultsName('sender_pid') +
      pyparsing.Suppress(']') +
      pyparsing.Suppress('<') +
      pyparsing.CharsNotIn('>').setResultsName('level') +
      pyparsing.Suppress('>') +
      pyparsing.Suppress('[') +
      pyparsing.CharsNotIn('{').setResultsName('facility') +
      pyparsing.Suppress('{') +
      pyparsing.Optional(pyparsing.CharsNotIn(
          '}').setResultsName('security_api')) +
      pyparsing.Suppress('}') +
      pyparsing.Optional(pyparsing.CharsNotIn(']:').setResultsName(
          'caller')) + pyparsing.Suppress(']:') +
      pyparsing.restOfLine().setResultsName('message') +
      _END_OF_LINE)

  _REPEATED_LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Suppress('--- last message repeated') +
      _INTEGER.setResultsName('times') +
      pyparsing.Suppress('time ---') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('log_liine', _LOG_LINE),
      ('repeated_log_line', _REPEATED_LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

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
      ParseError: if the structure cannot be parsed.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    # If the actual entry is a repeated entry, we take the basic information
    # from the previous entry, but use the timestamp from the actual entry.
    if key == 'log_liine':
      self._repeated_structure = structure

      message = self._GetStringValueFromStructure(structure, 'message')
    else:
      repeat_count = self._GetValueFromStructure(structure, 'times')

      structure = self._repeated_structure

      message = self._GetStringValueFromStructure(structure, 'message')
      message = 'Repeated {0:d} times: {1:s}'.format(repeat_count, message)

    event_data = MacOSSecuritydLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.caller = self._GetStringValueFromStructure(structure, 'caller')
    event_data.facility = self._GetValueFromStructure(structure, 'facility')
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.message = message or None
    event_data.security_api = self._GetValueFromStructure(
        structure, 'security_api')
    event_data.sender_pid = self._GetValueFromStructure(structure, 'sender_pid')
    event_data.sender = self._GetStringValueFromStructure(structure, 'sender')

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

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._repeated_structure = None

    return True


text_parser.TextLogParser.RegisterPlugin(MacOSSecuritydLogTextPlugin)
