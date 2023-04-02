# -*- coding: utf-8 -*-
"""Text parser plugin for PowerShell transcript log files."""

import copy
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class PowerShellTranscriptLogEventData(events.EventData):
  """PowerShell transcript log event data.

  Attributes:
    build_version (str): Build number of current version.
    clr_version (str): Common Language Runtime version.
    commands (str): Commands that were executed.
    compatible_versions (str): Compatible PowerShell versions.
    configuration_name (str): Configuration name.
    edition (str): PowerShell edition
    host_application (str): Application that executed the commands.
    machine (str): Hostname of machine.
    process_identifier (str): Process identifier.
    remoting_protocol_version (str): PowerShell remote management protocol
        version.
    runas_user (str): User context of execution.
    serialization_version (str): Serialization method version.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the PowerShell transcript.
    username (str): User that executed the commands.
    version (str): PowerShell version.
    ws_man_stack_version (str): WS-Management stack version
  """

  DATA_TYPE = 'powershell:transcript_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(PowerShellTranscriptLogEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.build_version = None
    self.clr_version = None
    self.commands = None
    self.compatible_versions = None
    self.configuration_name = None
    self.edition = None
    self.host_application = None
    self.machine = None
    self.process_identifier = None
    self.remoting_protocol_version = None
    self.runas_user = None
    self.serialization_version = None
    self.start_time = None
    self.username = None
    self.version = None
    self.ws_man_stack_version = None


class PowerShellTranscriptLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for PowerShell transcript log files."""

  NAME = 'powershell_transcript'

  DATA_FORMAT = 'PowerShell transcript event'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date and time values are formatted as: YYYYMMDDhhmmss
  # For example: 20220824124237
  _DATE_TIME = (_FOUR_DIGITS + _TWO_DIGITS + _TWO_DIGITS +
                _TWO_DIGITS + _TWO_DIGITS + _TWO_DIGITS)

  _SEPARATOR = pyparsing.Literal('**********************')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _SEPARATOR_LINE = _SEPARATOR + _END_OF_LINE

  _TRANSSCRIPT_START_LINE = pyparsing.Regex(r'.*Windows PowerShell.*\n')

  # A Metadata key always start with an uppercase character.
  _METADATA_KEY = pyparsing.Word(
      pyparsing.alphas.upper(), pyparsing.alphas + '- ')

  _METADATA_LINE = pyparsing.Combine(
      pyparsing.Suppress(_METADATA_KEY) + pyparsing.Suppress(':') +
      pyparsing.restOfLine() + _END_OF_LINE)

  _LOG_LINE = (
      pyparsing.NotAny(_SEPARATOR) +
      pyparsing.restOfLine().setResultsName('body') + _END_OF_LINE)

  _HEADER_GRAMMAR = (
      _SEPARATOR_LINE + _TRANSSCRIPT_START_LINE +
      _METADATA_LINE.setResultsName('date_time') +
      _METADATA_LINE.setResultsName('username') +
      _METADATA_LINE.setResultsName('runas_user') +
      _METADATA_LINE.setResultsName('configuration_name') +
      _METADATA_LINE.setResultsName('machine') +
      _METADATA_LINE.setResultsName('host_application') +
      _METADATA_LINE.setResultsName('process_identifier') +
      _METADATA_LINE.setResultsName('version') +
      _METADATA_LINE.setResultsName('edition') +
      _METADATA_LINE.setResultsName('compatible_versions') +
      _METADATA_LINE.setResultsName('build_version') +
      _METADATA_LINE.setResultsName('clr_version') +
      _METADATA_LINE.setResultsName('ws_man_stack_version') +
      _METADATA_LINE.setResultsName('remoting_protocol_version') +
      _METADATA_LINE.setResultsName('serialization_version') +
      _SEPARATOR_LINE)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('separator_line', _SEPARATOR_LINE)]

  VERIFICATION_GRAMMAR = _SEPARATOR_LINE + _TRANSSCRIPT_START_LINE

  VERIFICATION_LITERALS = ['Windows PowerShell']

  # TODO: handle footer with end time.

  def __init__(self):
    """Initializes instance attributes needed for processing."""
    super(PowerShellTranscriptLogTextPlugin, self).__init__()
    self._command_history = []
    self._event_data = None
    self._in_command_history = False

  def _ParseHeader(self, parser_mediator, text_reader):
    """Parses a text-log file header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    try:
      structure_generator = self._HEADER_GRAMMAR.scanString(
          text_reader.lines, maxMatches=1)
      structure, start, end = next(structure_generator)

    except StopIteration:
      structure = None

    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure or start != 0:
      raise errors.ParseError('No match found.')

    event_data = PowerShellTranscriptLogEventData()
    event_data.build_version = self._GetStringValueFromStructure(
        structure, 'build_version')
    event_data.clr_version = self._GetStringValueFromStructure(
        structure, 'clr_version')
    event_data.compatible_versions = self._GetStringValueFromStructure(
        structure, 'compatible_versions')
    event_data.configuration_name = self._GetStringValueFromStructure(
        structure, 'configuration_name')
    event_data.edition = self._GetStringValueFromStructure(
        structure, 'edition')
    event_data.host_application = self._GetStringValueFromStructure(
        structure, 'host_application')
    event_data.machine = self._GetStringValueFromStructure(
        structure, 'machine')
    event_data.process_identifier = self._GetStringValueFromStructure(
        structure, 'process_identifier')
    event_data.remoting_protocol_version = self._GetStringValueFromStructure(
        structure, 'remoting_protocol_version')
    event_data.runas_user = self._GetStringValueFromStructure(
        structure, 'runas_user')
    event_data.serialization_version = self._GetStringValueFromStructure(
        structure, 'serialization_version')
    event_data.username = self._GetStringValueFromStructure(
        structure, 'username')
    event_data.version = self._GetStringValueFromStructure(
        structure, 'version')
    event_data.ws_man_stack_version = self._GetStringValueFromStructure(
        structure, 'ws_man_stack_version')

    date_time_structure = self._GetStringValueFromStructure(
        structure, 'date_time')

    try:
      time_elements_structure = self._DATE_TIME.parseString(date_time_structure)
    except pyparsing.ParseException:
      raise errors.ParseError('Unable to parse date time.')

    event_data.start_time = self._ParseTimeElements(time_elements_structure)

    self._event_data = event_data
    self._in_command_history = True

    text_reader.SkipAhead(end)

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
    if self._in_command_history:
      if key == 'log_line':
        body = self._GetStringValueFromStructure(structure, 'body')
        if body:
          self._command_history.append(body)

      elif key == 'separator_line':
        event_data = copy.deepcopy(self._event_data)

        event_data.commands = '; '.join(self._command_history)

        parser_mediator.ProduceEventData(event_data)

        self._command_history = []
        self._in_command_history = False

    else:
      if key == 'log_line':
        body = self._GetStringValueFromStructure(structure, 'body')
        if ':' in body:
          date_time_structure = body.rsplit(':', maxsplit=1)[-1].strip()

          try:
            time_elements_structure = self._DATE_TIME.parseString(
                date_time_structure)
          except pyparsing.ParseException:
            raise errors.ParseError('Unable to parse date time.')

          self._event_data.start_time = self._ParseTimeElements(
              time_elements_structure)

      elif key == 'separator_line':
        self._in_command_history = True

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
      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string
      # when named token does not exists.

      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._command_history = []
    self._event_data = None
    self._in_command_history = False

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


text_parser.TextLogParser.RegisterPlugin(PowerShellTranscriptLogTextPlugin)
