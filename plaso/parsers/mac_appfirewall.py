# -*- coding: utf-8 -*-
"""This file contains a appfirewall.log (MacOS Firewall) parser."""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class MacAppFirewallLogEventData(events.EventData):
  """MacOS Firewall log event data.

  Attributes:
    action (str): action.
    agent (str): agent that save the log.
    computer_name (str): name of the computer.
    process_name (str): name of the entity that tried do the action.
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


class MacAppFirewallParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on appfirewall.log file."""

  NAME = 'mac_appfirewall_log'
  DESCRIPTION = 'Parser for appfirewall.log files.'

  _ENCODING = 'utf-8'

  # Define how a log line should look like.
  # Example: 'Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] '
  #          '<Info>: Dropbox: Allow (in:0 out:2)'
  # INFO: process_name is going to have a white space at the beginning.

  DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  FIREWALL_LINE = (
      DATE_TIME.setResultsName('date_time') +
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

  REPEATED_LINE = (
      DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('---').suppress() +
      pyparsing.CharsNotIn('---').setResultsName('process_name') +
      pyparsing.Literal('---').suppress())

  LINE_STRUCTURES = [
      ('logline', FIREWALL_LINE),
      ('repeated', REPEATED_LINE)]

  def __init__(self):
    """Initializes a parser object."""
    super(MacAppFirewallParser, self).__init__()
    self._last_month = 0
    self._previous_structure = None
    self._year_use = 0

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
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    # TODO: what if time_elements_tuple is None.
    month, day, hours, minutes, seconds = time_elements_tuple

    # Note that dfdatetime_time_elements.TimeElements will raise ValueError
    # for an invalid month.
    month = timelib.MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._year_use += 1

    return (self._year_use, month, day, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetTimeElementsTuple(structure)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    self._last_month = time_elements_tuple[1]

    # If the actual entry is a repeated entry, we take the basic information
    # from the previous entry, but use the timestamp from the actual entry.
    if key == 'logline':
      self._previous_structure = structure
    else:
      structure = self._previous_structure

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

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in ('logline', 'repeated'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseLogLine(parser_mediator, structure, key)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac AppFirewall log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    self._last_month = 0
    self._year_use = parser_mediator.GetEstimatedYear()

    try:
      structure = self.FIREWALL_LINE.parseString(line)
    except pyparsing.ParseException as exception:
      logger.debug((
          'Unable to parse file as a Mac AppFirewall log file with error: '
          '{0!s}').format(exception))
      return False

    action = self._GetValueFromStructure(structure, 'action')
    if action != 'creating /var/log/appfirewall.log':
      logger.debug(
          'Not a Mac AppFirewall log file, invalid action: {0!s}'.format(
              action))
      return False

    status = self._GetValueFromStructure(structure, 'status')
    if status != 'Error':
      logger.debug(
          'Not a Mac AppFirewall log file, invalid status: {0!s}'.format(
              status))
      return False

    time_elements_tuple = self._GetTimeElementsTuple(structure)

    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logger.debug((
          'Not a Mac AppFirewall log file, invalid date and time: '
          '{0!s}').format(time_elements_tuple))
      return False

    self._last_month = time_elements_tuple[1]

    return True


manager.ParsersManager.RegisterParser(MacAppFirewallParser)
