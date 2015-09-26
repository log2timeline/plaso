# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""
import re
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

  ENCODING = u'utf-8-sig'

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
      'microsecond': pyparsing.Regex(r'\d{3}\-\d{3}|\d{3}\+\d{3}|\d{6,7}').
                     setResultsName('microsecond'),
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
  LINE_GRAMMAR = (
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

  LINE_STRUCTURES = [
      ('log_entry', LINE_GRAMMAR + _PARSING_COMPONENTS['line_remainder']),
      ('log_entry_at_end',
       LINE_GRAMMAR +_PARSING_COMPONENTS['lastline_remainder'] +
       pyparsing.lineEnd)
      ]

  def __init__(self):
    """Initialize a parser object."""

    super(SCCMParser, self).__init__()

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
    match = self._PARSING_COMPONENTS['msg_left_delimiter'].match

    # Because logs files can lead with a partial event,
    # we can't assume that the first character (post-BOM)
    # in the file is the beginning of our match - so we
    # look for match anywhere in lines.
    if match in lines:
      return True
    return False

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object."""

    # Remove the microsecond dash or plus if it is present.
    # This is needed because SCCM logs may include a dash or
    # a plus character within the microseconds value.
    structure.microsecond = structure.microsecond.replace('-', '')
    structure.microsecond = structure.microsecond.replace('+', '')

    # Sometimes, SCCM logs will contain a seven-digit precision
    # (100s of nanoseconds). Taking six-digit precision because timestamps
    # are in microseconds.
    if len(structure.microsecond) > 6:
      structure.microsecond = structure.microsecond[0:6]

    try:
      microsecond = int(structure.microsecond)
    except ValueError:
      raise errors.TimestampError(
          u'Unable to parse log line due to non-int value of microseconds.')

    timestamp = timelib.Timestamp.FromTimeParts(
        structure.year, structure.month, structure.day, structure.hour,
        structure.minute, structure.second, microsecond)

    event_object = SCCMLogEvent(
        timestamp, 0, structure)

    parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(SCCMParser)
