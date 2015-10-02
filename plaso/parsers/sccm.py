# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""
import re
import datetime
import pyparsing

from plaso.events import text_events
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser
from plaso.lib import errors


class SCCMLogEvent(text_events.TextEvent):
  """Object class to represent SCCM log events """

  DATA_TYPE = u'software_management:sccm:log'


class SCCMParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Windows System Center Configuration Manager (SCCM) logs."""

  NAME = u'sccm'
  DESCRIPTION = u'Parser for SCCM logs files.'

  _ENCODING = u'utf-8-sig'

  # Increasing the buffer size as SCCM messages are commonly well larger
  # than the default value.
  BUFFER_SIZE = 16384

  LINE_STRUCTURES = []

  # PyParsing Components used to construct grammars for parsing lines.
  _PARSING_COMPONENTS = {
      'msg_left_delimiter': pyparsing.Literal(u'<![LOG['),
      'msg_right_delimiter': pyparsing.Literal(u']LOG]!><time="'),
      'year': text_parser.PyparsingConstants.YEAR.setResultsName('year'),
      'month': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
               setResultsName('month'),
      'day': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
             setResultsName('day'),
      'microsecond': pyparsing.Regex(r'\d{3,7}').
                     setResultsName('microsecond'),
      'utc_offset_minutes': pyparsing.Regex(r'[-+]\d{3}').
                            setResultsName('utc_offset_minutes'),
      'date_prefix': pyparsing.Literal(u'" date="').
                     setResultsName('date_prefix'),
      'component_prefix': pyparsing.Literal(u'" component="').
                          setResultsName('component_prefix'),
      'component': pyparsing.Word(pyparsing.alphanums).
                   setResultsName('component'),
      'text': pyparsing.Regex(r'.*?(?=(]LOG]!><time="))', re.DOTALL).
              setResultsName('text'),
      'line_remainder': pyparsing.Regex(r'.*?(?=(\<!\[LOG\[))', re.DOTALL).
                        setResultsName('line_remainder'),
      'lastline_remainder': pyparsing.restOfLine.
                            setResultsName('lastline_remainder'),
      'hour': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
              setResultsName('hour'),
      'minute': text_parser.PyparsingConstants.TWO_DIGITS.
                setResultsName('minute'),
      'second': text_parser.PyparsingConstants.TWO_DIGITS.
                setResultsName('second')
  }

  # Base grammar for individual log event lines.
  LINE_GRAMMAR_BASE = (
      _PARSING_COMPONENTS['msg_left_delimiter'] + _PARSING_COMPONENTS['text'] +
      _PARSING_COMPONENTS['msg_right_delimiter'] +
      _PARSING_COMPONENTS['hour'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['minute'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['second'] +
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['microsecond'] +
      _PARSING_COMPONENTS['date_prefix'] + _PARSING_COMPONENTS['month'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['day'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['year'] +
      _PARSING_COMPONENTS['component_prefix'] + _PARSING_COMPONENTS['component']
  )

  # Grammar for individual log event lines with a minutes offset from UTC.
  LINE_GRAMMAR_OFFSET = (
      _PARSING_COMPONENTS['msg_left_delimiter'] + _PARSING_COMPONENTS['text'] +
      _PARSING_COMPONENTS['msg_right_delimiter'] +
      _PARSING_COMPONENTS['hour'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['minute'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['second'] +
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['microsecond'] +
      _PARSING_COMPONENTS['utc_offset_minutes'] +
      _PARSING_COMPONENTS['date_prefix'] + _PARSING_COMPONENTS['month'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['day'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['year'] +
      _PARSING_COMPONENTS['component_prefix'] + _PARSING_COMPONENTS['component']
  )

  LINE_STRUCTURES = [
      ('log_entry', LINE_GRAMMAR_BASE + _PARSING_COMPONENTS['line_remainder']),
      ('log_entry_at_end',
       LINE_GRAMMAR_BASE +_PARSING_COMPONENTS['lastline_remainder'] +
       pyparsing.lineEnd),
      ('log_entry_offset',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS['line_remainder']),
      ('log_entry_offset_at_end',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS['lastline_remainder'] +
       pyparsing.lineEnd)
      ]

  def VerifyStructure(self, parser_mediator, lines):
    """Verify whether content corresponds to an SCCM log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      lines: A buffer that contains content from the file.

    Returns:
      Returns True if the passed buffer appears to contain content
      from an SCCM log file; returns False otherwise.
    """
    # Identify the token to which we attempt a match.
    match = self._PARSING_COMPONENTS[u'msg_left_delimiter'].match

    # Because logs files can lead with a partial event,
    # we can't assume that the first character (post-BOM)
    # in the file is the beginning of our match - so we
    # look for match anywhere in lines.
    if match in lines:
      return True
    return False

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Raises:
      TimestsampError: when a non-int value for microseconds is encountered.
    """
    # Sometimes, SCCM logs will exhibit a seven-digit sub-second precision
    # (100 nanosecond intervals). Using six-digit precision because
    # timestamps are in microseconds.
    if len(structure.microsecond) > 6:
      structure.microsecond = structure.microsecond[0:6]

    try:
      microsecond = int(structure.microsecond, 10)
    except ValueError:
      raise errors.TimestampError(
          u'Unable to read number of microseconds value.')

    # 3-digit precision is milliseconds,
    # so multiply by 1000 to convert to microseconds
    if len(structure.microsecond) == 3:
      microsecond = microsecond * 1000

    py_timestamp = datetime.datetime(
        year=structure.year, month=structure.month, day=structure.day,
        hour=structure.hour, minute=structure.minute,
        second=structure.second, microsecond=microsecond)

    # If an offset is given for the event, apply the offset to convert to UTC.
    if 'offset' in key:
      try:
        delta_seconds = int(structure.utc_offset_minutes[1:], 10) * 60
      except ValueError:
        raise ValueError(u'Unable to parse minute offset from UTC.')
      except IndexError:
        raise IndexError(u'Unable to parse minute offset from UTC.')
      if structure.utc_offset_minutes[0] == '-':
        delta_seconds = -delta_seconds
      py_timestamp = py_timestamp + datetime.timedelta(seconds=delta_seconds)

    timestamp = timelib.Timestamp.FromPythonDatetime(py_timestamp)
    event_object = SCCMLogEvent(timestamp, 0, structure)
    parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(SCCMParser)
