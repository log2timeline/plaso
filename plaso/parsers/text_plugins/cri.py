# -*- coding: utf-8 -*-
"""Text file parser plugin for Container Runtime Interface (CRI) log format.

This is a text-based log format used in kubernetes/GKE.

Also see:
  https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md
"""

import pyparsing

from dfdatetime import golang_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class CRIEventData(events.EventData):
  """CRI log event data.

  Attributes:
    event_datetime (dfdatetime.Golangtime): the datetime of the log message.
    message (str): the log message.
    stream (str): the log stream.  Currently only 'stdout' and 'stderr' are
        supported.
    tag (str): the log tag.  Currently only 'P' (partial) and 'F' (full) are
        supported.
  """
  DATA_TYPE = 'cri:container:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(CRIEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_datetime = None
    self.message = None
    self.stream = None
    self.tag = None


class CRITextPlugin(interface.TextPlugin):
  """Text file parser plugin for CRI log files."""

  NAME = 'cri_log'
  DATA_FORMAT = 'Container Runtime Interface log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4)

  _NINE_DIGITS = pyparsing.Word(pyparsing.nums, exact=9)

  # Date and time values are formatted as: 2016-10-06T00:17:09.669794202Z
  _DATE_AND_TIME = pyparsing.Combine(
      _FOUR_DIGITS + pyparsing.Literal('-') +
      _TWO_DIGITS + pyparsing.Literal('-') +
      _TWO_DIGITS + pyparsing.Literal('T').setParseAction(
          pyparsing.replace_with(' ')) +
      _TWO_DIGITS + pyparsing.Literal(':') +
      _TWO_DIGITS + pyparsing.Literal(':') +
      _TWO_DIGITS + pyparsing.Literal('.') +
      _NINE_DIGITS + pyparsing.Suppress(pyparsing.Literal('Z'))
  ).setResultsName('date_time')

  _STREAM = (
      pyparsing.Literal('stderr') ^ pyparsing.Literal('stdout')
  ).setResultsName('stream')

  # P indicates a partial log,
  # F indicates a complete or the end of a multiline log.
  _TAG = pyparsing.oneOf(['P', 'F']).setResultsName('tag')

  _LOG = (
      pyparsing.restOfLine() + pyparsing.Suppress(pyparsing.LineEnd())
  ).setResultsName('message')

  _LOG_LINE = _DATE_AND_TIME + _STREAM + _TAG + _LOG
  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

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
      golang_time_object = golang_time.GolangTime()
      golang_time_string = self._GetValueFromStructure(structure, 'date_time')
      golang_time_object.CopyFromDateTimeString(golang_time_string)

      event_data = CRIEventData()
      event_data.event_datetime = golang_time_object
      event_data.message = self._GetValueFromStructure(
          structure, 'message')[0]
      event_data.stream = self._GetValueFromStructure(structure, 'stream')
      event_data.tag = self._GetValueFromStructure(structure, 'tag')
      parser_mediator.ProduceEventData(event_data)

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(CRITextPlugin)
