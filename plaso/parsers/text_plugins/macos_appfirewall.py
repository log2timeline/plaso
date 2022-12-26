# -*- coding: utf-8 -*-
"""Text plugin for MacOS Application firewall log (appfirewall.log) files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSAppFirewallLogEventData(events.EventData):
  """MacOS Application firewall log (appfirewall.log) file event data.

  Attributes:
    action (str): action.
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    agent (str): agent that save the log.
    computer_name (str): name of the computer.
    process_name (str): name of the entity that tried to do the action.
    status (str): saved status action.
  """

  DATA_TYPE = 'macos:appfirewall_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSAppFirewallLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.added_time = None
    self.agent = None
    self.computer_name = None
    self.process_name = None
    self.status = None


class MacOSAppFirewallTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text plugin for MacOS Application firewall log (appfirewall.log) files."""

  NAME = 'mac_appfirewall_log'
  DATA_FORMAT = 'MacOS Application firewall log (appfirewall.log) file'

  ENCODING = 'utf-8'

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  # Define how a log line should look like.
  # Example: 'Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] '
  #          '<Info>: Dropbox: Allow (in:0 out:2)'
  # INFO: process_name is going to have a white space at the beginning.

  _DATE_TIME = (
      _THREE_LETTERS +
      _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _REPORTER_CHARACTERS = ''.join(
      [c for c in pyparsing.printables if c not in [':', '[', '<']])

  _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _AGENT = pyparsing.Combine(
      pyparsing.Word(_REPORTER_CHARACTERS) + pyparsing.Literal('[') +
      _PROCESS_IDENTIFIER + pyparsing.Literal(']'))

  _LOG_LINE_START = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Word(pyparsing.printables).setResultsName('computer_name') +
      _AGENT.setResultsName('agent'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _LOG_LINE_START +
      pyparsing.Suppress('<') +
      pyparsing.CharsNotIn('>').setResultsName('status') +
      pyparsing.Suppress('>:') +
      pyparsing.CharsNotIn(':').setResultsName('process_name') +
      pyparsing.Suppress(': ') +
      pyparsing.restOfLine().setResultsName('action') + _END_OF_LINE)

  # Repeated line.
  # Example: Nov 29 22:18:29 --- last message repeated 1 time ---

  _REPEATED_LOG_LINE_END = pyparsing.Suppress('---') + _END_OF_LINE

  _REPEATED_LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Suppress('---') + pyparsing.SkipTo(_REPEATED_LOG_LINE_END) +
      _REPEATED_LOG_LINE_END)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('repeated_log_line', _REPEATED_LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE_START + pyparsing.Literal(
      '<Error>: Logging: creating /var/log/appfirewall.log') + _END_OF_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(MacOSAppFirewallTextPlugin, self).__init__()
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
    if key == 'log_line':
      self._repeated_structure = structure
    else:
      structure = self._repeated_structure

    event_data = MacOSAppFirewallLogEventData()
    event_data.action = self._GetValueFromStructure(structure, 'action')
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.agent = self._GetValueFromStructure(structure, 'agent')
    event_data.computer_name = self._GetValueFromStructure(
        structure, 'computer_name')
    event_data.process_name = self._GetStringValueFromStructure(
        structure, 'process_name')
    event_data.status = self._GetValueFromStructure(structure, 'status')

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


text_parser.TextLogParser.RegisterPlugin(MacOSAppFirewallTextPlugin)
