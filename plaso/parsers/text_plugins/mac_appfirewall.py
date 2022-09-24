# -*- coding: utf-8 -*-
"""Text plugin for MacOS Application firewall log (appfirewall.log) files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacAppFirewallLogEventData(events.EventData):
  """MacOS Application firewall log (appfirewall.log) file event data.

  Attributes:
    action (str): action.
    agent (str): agent that save the log.
    computer_name (str): name of the computer.
    process_name (str): name of the entity that tried to do the action.
    status (str): saved status action.
  """

  DATA_TYPE = 'mac:appfirewall:line'

  def __init__(self):
    """Initializes event data."""
    super(MacAppFirewallLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.agent = None
    self.computer_name = None
    self.process_name = None
    self.status = None


class MacAppFirewallTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text plugin for MacOS Application firewall log (appfirewall.log) files."""

  NAME = 'mac_appfirewall_log'
  DATA_FORMAT = 'MacOS Application firewall log (appfirewall.log) file'

  ENCODING = 'utf-8'

  # Define how a log line should look like.
  # Example: 'Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] '
  #          '<Info>: Dropbox: Allow (in:0 out:2)'
  # INFO: process_name is going to have a white space at the beginning.

  _DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _FIREWALL_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Word(pyparsing.printables).setResultsName('computer_name') +
      pyparsing.Word(pyparsing.printables).setResultsName('agent') +
      pyparsing.Literal('<').suppress() +
      pyparsing.CharsNotIn('>').setResultsName('status') +
      pyparsing.Literal('>:').suppress() +
      pyparsing.CharsNotIn(':').setResultsName('process_name') +
      pyparsing.Literal(':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('action'))

  # Repeated line.
  # Example: Nov 29 22:18:29 --- last message repeated 1 time ---

  _REPEATED_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('---').suppress() +
      pyparsing.CharsNotIn('---').setResultsName('process_name') +
      pyparsing.Literal('---').suppress())

  _LINE_STRUCTURES = [
      ('logline', _FIREWALL_LINE),
      ('repeated', _REPEATED_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a text parser plugin."""
    super(MacAppFirewallTextPlugin, self).__init__()
    self._repeated_structure = None

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    # TODO: what if time_elements_tuple is None.
    month_string, day, hours, minutes, seconds = time_elements_tuple

    month = self._GetMonthFromString(month_string)

    self._UpdateYear(month)

    year = self._GetYear()

    return year, month, day, hours, minutes, seconds

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    try:
      time_elements_tuple = self._GetTimeElementsTuple(structure)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      return

    # If the actual entry is a repeated entry, we take the basic information
    # from the previous entry, but use the timestamp from the actual entry.
    if key == 'logline':
      self._repeated_structure = structure
    else:
      structure = self._repeated_structure

    event_data = MacAppFirewallLogEventData()
    event_data.action = self._GetValueFromStructure(structure, 'action')
    event_data.agent = self._GetValueFromStructure(structure, 'agent')
    event_data.computer_name = self._GetValueFromStructure(
        structure, 'computer_name')
    event_data.status = self._GetValueFromStructure(structure, 'status')

    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    process_name = self._GetValueFromStructure(structure, 'process_name')
    if process_name:
      event_data.process_name = process_name.strip()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

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

    self._ParseLogLine(parser_mediator, structure, key)

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
      parsed_structure = self._FIREWALL_LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    action = self._GetValueFromStructure(parsed_structure, 'action')
    if action != 'creating /var/log/appfirewall.log':
      return False

    status = self._GetValueFromStructure(parsed_structure, 'status')
    if status != 'Error':
      return False

    self._SetEstimatedYear(parser_mediator)

    try:
      time_elements_tuple = self._GetTimeElementsTuple(parsed_structure)
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except (TypeError, ValueError):
      return False

    return True


text_parser.SingleLineTextParser.RegisterPlugin(MacAppFirewallTextPlugin)
