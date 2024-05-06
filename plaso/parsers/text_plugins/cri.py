# -*- coding: utf-8 -*-
"""Text file parser plugin for Container Runtime Interface (CRI) log format.

This is a text-based log format used in kubernetes/GKE.

Also see:
  https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md
"""

import pyparsing

from dfdatetime import time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class CRIEventData(events.EventData):
  """CRI log event data.

  Attributes:
    body (str): the log message body.
    event_datetime (time_elements.TimeElementsInNanoseconds): the datetime of
        the log message.
    stream (str): the log stream.  Currently only 'stdout' and 'stderr' are
        supported.
    tag (str): the log tag.  Currently only 'P' (partial) and 'F' (full) are
        supported.
  """
  DATA_TYPE = 'cri:container:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(CRIEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.event_datetime = None
    self.stream = None
    self.tag = None


class CRITextPlugin(interface.TextPlugin):
  """Text file parser plugin for CRI log files."""

  NAME = 'cri_log'
  DATA_FORMAT = 'Container Runtime Interface log file'

  ENCODING = 'utf-8'

  # Date and time values are formatted as: 2016-10-06T00:17:09.669794202Z
  _DATE_AND_TIME = (
      pyparsing.Regex(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{1,9}Z')
  ).setResultsName('date_time')

  _STREAM = (
      pyparsing.Literal('stderr') ^ pyparsing.Literal('stdout')
  ).setResultsName('stream')

  # P indicates a partial log,
  # F indicates a complete or the end of a multiline log.
  _TAG = pyparsing.oneOf(['P', 'F']).setResultsName('tag')

  _LOG = (
      pyparsing.restOfLine() + pyparsing.Suppress(pyparsing.LineEnd())
  ).setResultsName('body')

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
      date_time = time_elements.TimeElementsInNanoseconds()
      date_time.CopyFromStringISO8601(self._GetValueFromStructure(
          structure, 'date_time'))
      event_data = CRIEventData()
      event_data.event_datetime = date_time
      event_data.body = self._GetValueFromStructure(
          structure, 'body')[0]
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
