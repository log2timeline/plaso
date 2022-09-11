# -*- coding: utf-8 -*-
"""Text parser plugin for MacOS security daemon (securityd) log files.

Also see:
  https://opensource.apple.com/source/Security/Security-55471/sec/securityd
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSSecuritydLogEventData(events.EventData):
  """MacOS securityd log event data.

  Attributes:
    caller (str): caller, consists of two hex numbers.
    facility (str): facility.
    level (str): priority level.
    message (str): message.
    security_api (str): name of securityd function.
    sender (str): name of the sender.
    sender_pid (int): process identifier of the sender.
  """

  DATA_TYPE = 'mac:securityd:line'

  def __init__(self):
    """Initializes event data."""
    super(MacOSSecuritydLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller = None
    self.facility = None
    self.level = None
    self.message = None
    self.security_api = None
    self.sender = None
    self.sender_pid = None


class MacOSSecuritydLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for MacOS security daemon (securityd) log files."""

  NAME = 'mac_securityd'
  DATA_FORMAT = 'MacOS security daemon (securityd) log file'

  ENCODING = 'utf-8'

  _DEFAULT_YEAR = 2012

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _SECURITYD_LINE = (
      DATE_TIME.setResultsName('date_time') +
      pyparsing.CharsNotIn('[').setResultsName('sender') +
      pyparsing.Literal('[').suppress() +
      text_parser.PyparsingConstants.PID.setResultsName('sender_pid') +
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
      DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('--- last message repeated').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('times') +
      pyparsing.Literal('time ---').suppress())

  _LINE_STRUCTURES = [
      ('logline', _SECURITYD_LINE),
      ('repeated', _REPEATED_LINE)]

  def __init__(self):
    """Initializes a text parser plugin."""
    super(MacOSSecuritydLogTextPlugin, self).__init__()
    self._last_month = None
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
    month = self._MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._year_use += 1

    return (self._year_use, month, day, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
      key (str): name of the parsed structure.
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

    if key == 'logline':
      self._previous_structure = structure
      message = self._GetValueFromStructure(structure, 'message')
    else:
      repeat_count = self._GetValueFromStructure(structure, 'times')
      previous_message = self._GetValueFromStructure(
          self._previous_structure, 'message')
      message = 'Repeated {0:d} times: {1:s}'.format(
          repeat_count, previous_message)
      structure = self._previous_structure

    # It uses CarsNotIn structure which leaves whitespaces
    # at the beginning of the sender and the caller.
    caller = self._GetValueFromStructure(structure, 'caller')
    if caller:
      caller = caller.strip()

    # TODO: move this to formatter.
    if not caller:
      caller = 'unknown'

    sender = self._GetValueFromStructure(structure, 'sender')
    if sender:
      sender = sender.strip()

    event_data = MacOSSecuritydLogEventData()
    event_data.caller = caller
    event_data.facility = self._GetValueFromStructure(structure, 'facility')
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.message = message
    event_data.security_api = self._GetValueFromStructure(
        structure, 'security_api', default_value='unknown')
    event_data.sender_pid = self._GetValueFromStructure(structure, 'sender_pid')
    event_data.sender = sender

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
    if key not in ('logline', 'repeated'):
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
      parsed_structure = self._SECURITYD_LINE.parseString(line)
    except pyparsing.ParseException:
      parsed_structure = None

    if not parsed_structure:
      return False

    self._last_month = 0
    self._year_use = parser_mediator.GetEstimatedYear()

    time_elements_tuple = self._GetTimeElementsTuple(parsed_structure)

    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      return False

    self._last_month = time_elements_tuple[1]

    return True


text_parser.SingleLineTextParser.RegisterPlugin(MacOSSecuritydLogTextPlugin)
