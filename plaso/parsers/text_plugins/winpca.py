# -*- coding: utf-8 -*-
"""Text parser plugin for Windows PCA Log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class WinPCAEventData(events.EventData):
  """Windows PCA (Program Compatibility Assistant) event data.

  Attributes:
    body (str): message body.
    description (str): Description of the executable.
    exit_code (str): Final result of the execution.
    last_execution_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    program_id (str): Program ID.
    run_status (str): Execution status.
    vendor (str): Software vendor.
    version (str): Software version.
  """

  DATA_TYPE = 'windows:pca_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(WinPCAEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.description = None
    self.exit_code = None
    self.last_execution_time = None
    self.program_id = None
    self.run_status = None
    self.vendor = None
    self.version = None

class WinPCALogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Windows PCA Log files."""

  NAME = 'winpca'
  DATA_FORMAT = 'Windows PCA log file'

  _SEPARATOR = pyparsing.Suppress('|')

  _SKIP_TO_SEPARATOR = pyparsing.SkipTo('|')

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _DATE = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _TIME = pyparsing.Group(
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _THREE_DIGITS)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LAUNCH_DIC_LOG_LINE = (
      pyparsing.SkipTo('|').setResultsName('exec') +
      _SEPARATOR +
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time') +
      _END_OF_LINE
  )

  _DB0_LOG_LINE = (
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('run_status') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('exec') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('description') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('vendor') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('version') +
      _SEPARATOR +
      _SKIP_TO_SEPARATOR.setResultsName('program_id') +
      _SEPARATOR +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('exit_code') +
      _END_OF_LINE
  )

  _LINE_STRUCTURES = [
      ('launch_dic_log_line', _LAUNCH_DIC_LOG_LINE),
      ('db0_log_line', _DB0_LOG_LINE)]

  VERIFICATION_GRAMMAR = (_LAUNCH_DIC_LOG_LINE ^ _DB0_LOG_LINE)

  def __init__(self):
    """Initializes a text parser plugin.

    Attributes:
      _use_local_time (bool): Passed to dfdatetime_time_elements
          to indicate whether or not the times are in UTC.
    """
    super(WinPCALogTextPlugin, self).__init__()
    self._use_local_time = False

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """
    event_data = WinPCAEventData()
    event_data.body = self._GetValueFromStructure(structure, 'exec')
    event_data.last_execution_time = self._ParseTimeElements(structure)

    event_data.run_status = self._GetValueFromStructure(
        structure, 'run_status')
    event_data.description = self._GetValueFromStructure(
        structure, 'description')
    event_data.vendor = self._GetValueFromStructure(
        structure, 'vendor')
    event_data.version = self._GetValueFromStructure(
        structure, 'version')
    event_data.program_id = self._GetValueFromStructure(
        structure, 'program_id')
    event_data.exit_code = self._GetValueFromStructure(
        structure, 'exit_code')

    parser_mediator.ProduceEventData(event_data)

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
    self._ParseLogLine(parser_mediator, structure)

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
      date_elements_structure = self._GetValueFromStructure(structure, 'date')
      time_elements_structure = self._GetValueFromStructure(structure, 'time')

      year, month, day_of_month = date_elements_structure
      hours, minutes, seconds, milliseconds = time_elements_structure

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = self._use_local_time

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._use_local_time = False

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(WinPCALogTextPlugin)
