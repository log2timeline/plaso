# -*- coding: utf-8 -*-
"""Text parser plugin for Apple ps.txt files from sysdiagnose files."""

import datetime
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import dateless_helper
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class ApplePSTxtEventData(events.EventData):
  """Apple ps.txt event data.

  Attributes:
    command (str): Command and arguments that launched the process.
    control_terminal_name (str): control terminal name (two letter
        abbreviation).
    cpu (str): % of cpu usage.
    flags (str): Process flags, in hexadecimal.
    memory (str): % of memory usage.
    nice_value (str): nice_value.
    persona (str): persona.
    process_identifier (str): process identifier.
    parent_process_identifier (str): process_parent_identifier
    resident_set_size (str): Resident Set Size
    scheduling_priority (str): Scheduling Priority
    start_time (dfdatetime.DateTimeValues): Start time of the process.
    symbolic_process_state (str): Symbolic process state.
    up_time (str): Accumulated cpu time.
    user (str): User name.
    user_identifier (str): User identifier
    virtual_size (str): Virtual size in kilobytes.
    wait_channel (str): Wait channel.
  """

  DATA_TYPE = 'apple:pstxt:entry'

  def __init__(self):
    """Initializes event data."""
    super(ApplePSTxtEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.control_terminal_name = None
    self.cpu = None
    self.flags = None
    self.memory = None
    self.nice_value = None
    self.persona = None
    self.process_identifier = None
    self.parent_process_identifier = None
    self.resident_set_size = None
    self.scheduling_priority = None
    self.start_time = None
    self.symbolic_process_state = None
    self.up_time = None
    self.user = None
    self.user_identifier = None
    self.virtual_size = None
    self.wait_channel = None


class ApplePSTextPlugin(
  interface.TextPlugin, dateless_helper.DateLessLogFormatHelper):
  """Text parser plugin for Apple ps.txt files."""

  NAME = 'apple_ps_txt'
  DATA_FORMAT = 'Apple ps.txt files'

  _DATE = (
      pyparsing.Word(pyparsing.nums, min=1, max=2).set_results_name('day') +
      pyparsing.Word(pyparsing.alphanums, exact=3).set_results_name('month') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('year')
  )

  _TIME = (
      pyparsing.Word(pyparsing.nums, min=1, max=2).set_results_name('hours') +
      pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('minutes') +
      pyparsing.one_of('AM PM').set_results_name('ampm')
  )

  _WEEKDAY = (
      pyparsing.Word(pyparsing.alphas, exact=3).set_results_name('weekday') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('hours') +
      pyparsing.one_of('AM PM').set_results_name('ampm')
  )

  _HEADER = (
      pyparsing.Literal('USER             UID PRSNA   PID  PPID        F  %CPU '
                        '%MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED'
                        '      TIME COMMAND') + pyparsing.LineEnd())

  _COMMAND = pyparsing.OneOrMore(
      pyparsing.Word(pyparsing.printables),
      stop_on=pyparsing.LineEnd()).set_parse_action(' '.join)

  _LOG_LINE = (
      pyparsing.Word(pyparsing.alphanums + '_').set_results_name('user') +
      pyparsing.Word(pyparsing.nums).set_results_name('user_identifier') +
      pyparsing.Word(pyparsing.nums + '-').set_results_name('persona') +
      pyparsing.Word(pyparsing.nums).set_results_name('process_identifier') +
      pyparsing.Word(pyparsing.nums).set_results_name(
        'parent_process_identifier') +
      pyparsing.Word(pyparsing.alphanums).set_results_name('flags') +
      pyparsing.Word(pyparsing.nums + '.').set_results_name('cpu') +
      pyparsing.Word(pyparsing.nums + '.').set_results_name('memory') +
      pyparsing.Word(pyparsing.nums).set_results_name('scheduling_priority') +
      pyparsing.Word(pyparsing.nums).set_results_name('nice_value') +
      pyparsing.Word(pyparsing.nums).set_results_name('virtual_size') +
      pyparsing.Word(pyparsing.nums).set_results_name('resident_set_size') +
      pyparsing.Word(pyparsing.nums + '-').set_results_name('wait_channel') +
      pyparsing.Word(pyparsing.alphanums + '?').set_results_name(
        'control_terminal_name') +
      pyparsing.Word(pyparsing.alphanums).set_results_name(
        'symbolic_process_state') +
      pyparsing.Word(pyparsing.alphanums + ':').set_results_name('start_time') +
      pyparsing.Word(pyparsing.nums + '.:').set_results_name('up_time') +
      _COMMAND.set_results_name('command')
  )

  _LINE_STRUCTURES = [('log_line', _LOG_LINE), ('header', _HEADER)]

  VERIFICATION_GRAMMAR = pyparsing.Suppress(_HEADER) + _LOG_LINE

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
    if key == 'log_line':
      event_data = ApplePSTxtEventData()
      event_data.user = self._GetValueFromStructure(structure, 'user')
      event_data.user_identifier = self._GetValueFromStructure(
        structure, 'user_identifier')
      event_data.persona = self._GetValueFromStructure(structure, 'persona')
      event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
      event_data.parent_process_identifier = self._GetValueFromStructure(
        structure, 'parent_process_identifier')
      event_data.flags = self._GetValueFromStructure(structure, 'flags')
      event_data.cpu = self._GetValueFromStructure(structure, 'cpu')
      event_data.memory = self._GetValueFromStructure(structure, 'memory')
      event_data.scheduling_priority = self._GetValueFromStructure(
        structure, 'scheduling_priority')
      event_data.nice_value = self._GetValueFromStructure(
        structure, 'nice_value')
      event_data.virtual_size = self._GetValueFromStructure(
        structure, 'virtual_size')
      event_data.resident_set_size = self._GetValueFromStructure(
        structure, 'resident_set_size')
      event_data.wait_channel = self._GetValueFromStructure(
        structure, 'wait_channel')
      event_data.control_terminal_name = self._GetValueFromStructure(
        structure, 'control_terminal_name')
      event_data.symbolic_process_state = self._GetValueFromStructure(
        structure, 'symbolic_process_state')
      event_data.up_time = self._GetValueFromStructure(structure, 'up_time')
      event_data.command = self._GetValueFromStructure(structure, 'command')

      start_time_string = self._GetValueFromStructure(
        structure, 'start_time')
      event_data.start_time = self._ParseStartTime(start_time_string)

      parser_mediator.ProduceEventData(event_data)

  def _ParseStartTime(self, start_time_string):
    """Parses the start time element of a log line.

    Args:
      start_time_string (str): start time element of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      # Case where it's just a time
      if (
          start_time_string[0] in pyparsing.nums
          and start_time_string[-1] == 'M'):
        parsed_elements = self._TIME.parse_string(start_time_string)

        hours = int(parsed_elements.get('hours'))
        minutes = int(parsed_elements.get('minutes'))
        ampm = parsed_elements.get('ampm')
        if ampm == 'PM':
          hours += 12
        if hours == 24:
          hours = 0

        # Retrieve year, month, day from dateless helper
        year = self._date[0]
        month = self._date[1]
        day = self._date[2]

        time_elements_tuple = (year, month, day, hours, minutes, 0)

      # Case where it is a weekday with a time
      elif start_time_string[0] in pyparsing.alphas:
        parsed_elements = self._WEEKDAY.parse_string(start_time_string)

        hours = int(parsed_elements.get('hours'))
        weekday_string = parsed_elements.get('weekday')
        weekday = self._GetWeekDayFromString(weekday_string)
        ampm = parsed_elements.get('ampm')
        if ampm == 'PM':
          hours += 12
        if hours == 24:
          hours = 0

        # Retrieve year, month, day from dateless helper
        year = self._date[0]
        month = self._date[1]
        day = self._date[2]

        date_from_file = datetime.datetime(year, month, day)
        days_before = (date_from_file.isoweekday() - weekday + 7) % 7
        date_of_record = date_from_file - datetime.timedelta(days=days_before)

        time_elements_tuple = (
            date_of_record.year, date_of_record.month, date_of_record.day,
            hours, 0, 0)

      # Case where it is a date with no time
      elif start_time_string[0] in pyparsing.nums:
        parsed_elements = self._DATE.parse_string(start_time_string)

        year = int(parsed_elements.get('year')) + 2000
        month_str = parsed_elements.get('month')
        month = self._GetMonthFromString(month_str)
        day = int(parsed_elements.get('day'))

        time_elements_tuple = (year, month, day, 0, 0, 0)

      else:
        raise errors.ParseError('start time was not in an expected format.')

      return dfdatetime_time_elements.TimeElements(
        time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
        f'Unable to parse time elements with error: {exception!s}')

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

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

    start_time_string = self._GetValueFromStructure(
        structure, 'start_time')

    try:
      self._ParseStartTime(start_time_string)
    except errors.ParseError:
      return False

    # Retrieve the data from the file's metadata
    self._SetEstimatedDate(parser_mediator)

    return True


text_parser.TextLogParser.RegisterPlugin(ApplePSTextPlugin)
