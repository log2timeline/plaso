"""Text parser plugin for Anydesk trace log (ad.trace) files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface

class AnyDeskAdTraceLogEventData(events.EventData):
  """AnyDesk trace log event data.

  Attributes:
    application_name (str): application source, such as "back", "ctrl", "front".
    function (str): Source/Activity that generates the event
    log_level (str): type of log record, such as "info", "warning", "error".
    message (str): Detailed message.
    pid (int): Process identifier from where the event is generated
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry was
        recorded.
    thread_identifier (int): Thread identifier from where the event is
        generated.
  """

  DATA_TYPE = 'anydesk:adtrace_log:entry'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.application_name = None
    self.function = None
    self.log_level = None
    self.message = None
    self.pid = None
    self.recorded_time = None
    self.thread_identifier = None

class AnyDeskAdTraceLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for AnyDesk trace log (ad.trace) files."""

  NAME = 'anydesk_adtrace'
  DATA_FORMAT = 'AnyDesk trace log (ad.trace) file'
  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _LOG_LEVEL = pyparsing.Word(pyparsing.alphas).setResultsName('loglevel')

  # Date and time values are formatted as: 2022-12-29 13:34:22.945
  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS +
      _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName('date_time')

  _APPNAME = pyparsing.Word(pyparsing.alphas).setResultsName('application_name')

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FUNCTION_MESSAGE = (
    pyparsing.Word(pyparsing.alphanums + '.' + '_').setResultsName('function') +
    pyparsing.Suppress("-") +
    pyparsing.restOfLine().setResultsName('message')
  )

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _BASIC_LOG_FORMAT_LINE = (
    _LOG_LEVEL +
    _DATE_TIME +
    _APPNAME +
    _INTEGER.setResultsName('pid') +
    _INTEGER.setResultsName('thread_identifier') +
    _FUNCTION_MESSAGE +
    _END_OF_LINE
  )

  _SEPARATOR_LINE = pyparsing.Literal("* * * * * * * * * * * * * * * * * *")

  _LINE_STRUCTURES = [
      ('basic_log_format', _BASIC_LOG_FORMAT_LINE),
      ('_separator_line',_SEPARATOR_LINE)]

  VERIFICATION_GRAMMAR = (
      pyparsing.ZeroOrMore(_END_OF_LINE) + _BASIC_LOG_FORMAT_LINE)

  VERIFICATION_LITERALS = None

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

    event_data = AnyDeskAdTraceLogEventData()

    log_level = self._GetValueFromStructure(structure, 'loglevel')
    if not log_level in ('error', 'info', 'warning'):
      return

    event_data.log_level = log_level
    event_data.application_name = self._GetValueFromStructure(
        structure, 'application_name')
    event_data.function = self._GetValueFromStructure(structure, 'function')
    event_data.message = self._GetValueFromStructure(structure, 'message')
    event_data.pid = self._GetValueFromStructure(structure, 'pid')
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
    event_data.thread_identifier = self._GetValueFromStructure(
        structure, 'thread_identifier')

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
      (year, month, day, hours, minutes, seconds, milliseconds) = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day, hours, minutes, seconds, milliseconds)
      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(AnyDeskAdTraceLogTextPlugin)
