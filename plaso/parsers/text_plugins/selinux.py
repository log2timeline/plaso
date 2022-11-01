# -*- coding: utf-8 -*-
"""Text parser plugin for SELinux audit log (audit.log) files.

audit.log log line example:

type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

Where msg=audit(1105758604.519:420) contains the number of seconds since
January 1, 1970 00:00:00 UTC and the number of milliseconds after the dot
for example: "seconds: 1105758604, milliseconds: 519".

The number after the timestamp (420 in the example) is a 'serial number'
that can be used to correlate multiple logs generated from the same event.
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SELinuxLogEventData(events.EventData):
  """SELinux log event data.

  Attributes:
    audit_type (str): audit type.
    body (str): body of the log line.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    pid (int): process identifier (PID) that created the SELinux log line.
  """

  DATA_TYPE = 'selinux:line'

  def __init__(self):
    """Initializes event data."""
    super(SELinuxLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.audit_type = None
    self.body = None
    self.last_written_time = None
    self.pid = None


class SELinuxTextPlugin(interface.TextPlugin):
  """Text parser plugin for SELinux audit log (audit.log) files."""

  NAME = 'selinux'
  DATA_FORMAT = 'SELinux audit log (audit.log) file'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.ConvertTokenToInteger)

  _KEY_VALUE_GROUP = pyparsing.Group(
      pyparsing.Word(pyparsing.alphanums) +
      pyparsing.Suppress('=') + (
          pyparsing.QuotedString('"') ^
          pyparsing.Word(pyparsing.printables)))

  _KEY_VALUE_DICT = pyparsing.Dict(
      pyparsing.ZeroOrMore(_KEY_VALUE_GROUP))

  _BODY_GROUP = pyparsing.Group(
      pyparsing.Empty() + pyparsing.restOfLine)

  _TIMESTAMP = (_INTEGER + pyparsing.Suppress('.') + _INTEGER)

  _MSG_GROUP = pyparsing.Group(
      pyparsing.Suppress('msg=audit(') +
      _TIMESTAMP.setResultsName('timestamp') +
      pyparsing.Suppress(':') + _INTEGER +
      pyparsing.Suppress('):'))

  _TYPE_GROUP = pyparsing.Group(
      pyparsing.Literal('type') + pyparsing.Suppress('=') + (
          pyparsing.Word(pyparsing.srange('[A-Z_]')) ^
          pyparsing.Regex(r'UNKNOWN\[[0-9]+\]')))

  _TYPE_AVC_GROUP = pyparsing.Group(
      pyparsing.Literal('type') + pyparsing.Suppress('=') + (
          pyparsing.Word('AVC') ^ pyparsing.Word('USER_AVC')))

  # A log line is formatted as: type=TYPE msg=audit([0-9]+\.[0-9]+:[0-9]+): .*
  _LOG_LINE = pyparsing.Dict(
      _TYPE_GROUP + _MSG_GROUP.setResultsName('msg') + _BODY_GROUP)

  _LINE_STRUCTURES = [('line', _LOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _GetDateTimeValueFromStructure(self, msg_structure):
    """Retrieves a date and time value from a Pyparsing structure.

    Args:
      msg_structure (pyparsing.ParseResults): tokens from a parsed log line.

    Returns:
      dfdatetime.TimeElements: date and time value or None if not available.
    """
    timestamp_structure = self._GetValueFromStructure(
        msg_structure, 'timestamp')

    seconds, milliseconds = timestamp_structure

    timestamp = (seconds * 1000) + milliseconds

    return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

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

    msg_structure = self._GetValueFromStructure(structure, 'msg')
    if not msg_structure:
      parser_mediator.ProduceExtractionWarning(
          'missing msg value: {0!s}'.format(structure))
      return

    body_text = structure[2][0]

    try:
      # Try to parse the body text as key value pairs. Note that not
      # all log lines will be properly formatted key value pairs.
      body_structure = self._KEY_VALUE_DICT.parseString(body_text)
    except pyparsing.ParseException:
      body_structure = pyparsing.ParseResults()

    event_data = SELinuxLogEventData()
    event_data.audit_type = self._GetValueFromStructure(structure, 'type')
    event_data.body = body_text
    event_data.last_written_time = self._GetDateTimeValueFromStructure(
        msg_structure)
    event_data.pid = self._GetValueFromStructure(body_structure, 'pid')

    parser_mediator.ProduceEventData(event_data)

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
      parsed_structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    msg_structure = self._GetValueFromStructure(parsed_structure, 'msg')

    return bool(msg_structure)


text_parser.SingleLineTextParser.RegisterPlugin(SELinuxTextPlugin)
