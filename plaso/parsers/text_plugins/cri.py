# -*- coding: utf-8 -*-
"""Text file parser plugin for Container Runtime Interface log files."""

import pyparsing

from dfdatetime import time_elements


class CRIEventData(events.EventData):
  """CRI event data.

  Attributes:
    event_datetime (dfdatetime.Golangtime): the datetime of the log message.
    log_message (str): the log message.
    stream (str): the log stream.  Currently stdout and stderr.
    tag (str): the log tag.  Currently only P (partial) and F (full) are supported.
  """

class CRITextPlugin(interface.TextPlugin):
  """Text file parser plugin for Container Runtime Interface log files."""

  NAME = 'cri'
  DATA_FORMAT = 'Container Runtime Interface log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _NINE_DIGITS = pyparsing.Word(pyparsing.nums, exact=9).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date and time values are formatted as: 2016-10-06T00:17:09.669794202Z
  _DATE_AND_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('T') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _NINE_DIGITS + pyparsing.Suppress('Z')).setResultsName('date_time')

  _STREAM = (
      pyparsing.Literal('stderr') ^ pyparsing.Literal('stdout')
  ).setResultsName('stream')

  # P indicates a partial log, F indicates a complete or the end of a multiline log.
  _TAG = pyparsing.oneOf(['P', 'F']).setResultsName('tag')

  _LOG = (
      pyparsing.restOfLine() + pyparsing.Suppress(pyparsing.LineEnd())
  ).setResultsName('message')

  _LOG_LINE = _DATE_AND_TIME + _STREAM + _TAG + _LOG
  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

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
      (year, month, day_of_month, hours, minutes, seconds, nanoseconds) = (
          time_elements_structure)

      return dfdatetime_time_elements.TimeElementsInNanoseconds(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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
      time_elements_structure = self._GetValueFromStructure(
          structure, 'date_time')

      event_data = CRIEventData()
      event_data.event_datetime = self._ParseTimeElements(time_elements_structure)
      event_data.log_message = self._GetValueFromStructure(structure, 'log_message')
      event_data.stream = self._GetValueFromStructure(strucutre, 'stream')
      event_data.tag = self._GetValueFromStructure(structure, 'tag')
