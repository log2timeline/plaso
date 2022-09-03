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
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SELinuxLogEventData(events.EventData):
  """SELinux log event data.

  Attributes:
    audit_type (str): audit type.
    body (str): body of the log line.
    pid (int): process identifier (PID) that created the SELinux log line.
  """

  DATA_TYPE = 'selinux:line'

  def __init__(self):
    """Initializes event data."""
    super(SELinuxLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.audit_type = None
    self.body = None
    self.pid = None


class SELinuxTextPlugin(interface.TextPlugin):
  """Text parser plugin for SELinux audit log (audit.log) files."""

  NAME = 'selinux'
  DATA_FORMAT = 'SELinux audit log (audit.log) file'

  _SELINUX_KEY_VALUE_GROUP = pyparsing.Group(
      pyparsing.Word(pyparsing.alphanums).setResultsName('key') +
      pyparsing.Suppress('=') + (
          pyparsing.QuotedString('"') ^
          pyparsing.Word(pyparsing.printables)).setResultsName('value'))

  _SELINUX_KEY_VALUE_DICT = pyparsing.Dict(
      pyparsing.ZeroOrMore(_SELINUX_KEY_VALUE_GROUP))

  _SELINUX_BODY_GROUP = pyparsing.Group(
      pyparsing.Empty().setResultsName('key') +
      pyparsing.restOfLine.setResultsName('value'))

  _SELINUX_MSG_GROUP = pyparsing.Group(
      pyparsing.Literal('msg').setResultsName('key') +
      pyparsing.Suppress('=audit(') +
      pyparsing.Word(pyparsing.nums).setResultsName('seconds') +
      pyparsing.Suppress('.') +
      pyparsing.Word(pyparsing.nums).setResultsName('milliseconds') +
      pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums).setResultsName('serial') +
      pyparsing.Suppress('):'))

  _SELINUX_TYPE_GROUP = pyparsing.Group(
      pyparsing.Literal('type').setResultsName('key') +
      pyparsing.Suppress('=') + (
          pyparsing.Word(pyparsing.srange('[A-Z_]')) ^
          pyparsing.Regex(r'UNKNOWN\[[0-9]+\]')).setResultsName('value'))

  _SELINUX_TYPE_AVC_GROUP = pyparsing.Group(
      pyparsing.Literal('type').setResultsName('key') +
      pyparsing.Suppress('=') + (
          pyparsing.Word('AVC') ^
          pyparsing.Word('USER_AVC')).setResultsName('value'))

  # A log line is formatted as: type=TYPE msg=audit([0-9]+\.[0-9]+:[0-9]+): .*
  _SELINUX_LOG_LINE = pyparsing.Dict(
      _SELINUX_TYPE_GROUP +
      _SELINUX_MSG_GROUP +
      _SELINUX_BODY_GROUP)

  _LINE_STRUCTURES = [('line', _SELINUX_LOG_LINE)]

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
    if key != 'line':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    msg_value = self._GetValueFromStructure(structure, 'msg')
    if not msg_value:
      parser_mediator.ProduceExtractionWarning(
          'missing msg value: {0!s}'.format(structure))
      return

    try:
      seconds = int(msg_value[0], 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of seconds in msg value: {0!s}'.format(
              structure))
      return

    try:
      milliseconds = int(msg_value[1], 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of milliseconds in msg value: {0!s}'.format(
              structure))
      return

    timestamp = ((seconds * 1000) + milliseconds) * 1000
    body_text = structure[2][0]

    try:
      # Try to parse the body text as key value pairs. Note that not
      # all log lines will be properly formatted key value pairs.
      body_structure = self._SELINUX_KEY_VALUE_DICT.parseString(body_text)
    except pyparsing.ParseException:
      body_structure = pyparsing.ParseResults()

    event_data = SELinuxLogEventData()
    event_data.audit_type = self._GetValueFromStructure(structure, 'type')
    event_data.body = body_text
    event_data.pid = self._GetValueFromStructure(body_structure, 'pid')

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

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
      parsed_structure = self._SELINUX_LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      parsed_structure = {}

    return 'type' in parsed_structure and 'msg' in parsed_structure


text_parser.PyparsingSingleLineTextParser.RegisterPlugin(SELinuxTextPlugin)
