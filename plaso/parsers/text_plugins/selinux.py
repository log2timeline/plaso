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
from plaso.lib import definitions
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
      lambda tokens: int(tokens[0], 10))

  _KEY_VALUE_GROUP = pyparsing.Group(
      pyparsing.Word(pyparsing.alphanums) +
      pyparsing.Suppress('=') + (
          pyparsing.QuotedString('"') ^
          pyparsing.Word(pyparsing.printables)))

  _KEY_VALUE_DICT = pyparsing.Dict(
      pyparsing.ZeroOrMore(_KEY_VALUE_GROUP))

  _TIMESTAMP = pyparsing.Group(
      _INTEGER + pyparsing.Suppress('.') + _INTEGER)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # A log line is formatted as: type=TYPE msg=audit([0-9]+\.[0-9]+:[0-9]+): .*
  _LOG_LINE = (
      pyparsing.Suppress('type=') + (
          pyparsing.Word(pyparsing.srange('[A-Z_]')) ^
          pyparsing.Regex(r'UNKNOWN\[[0-9]+\]')).setResultsName('type') +
      pyparsing.Suppress('msg=audit(') +
      _TIMESTAMP.setResultsName('timestamp') +
      pyparsing.Suppress(':') + _INTEGER + pyparsing.Suppress('):') +
      pyparsing.restOfLine().setResultsName('body') +
      _END_OF_LINE)

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
      time_elements_structure = self._GetValueFromStructure(
          structure, 'timestamp')

      # Try to parse the body text as key value pairs. Note that not
      # all log lines will be properly formatted key value pairs.
      body = self._GetValueFromStructure(structure, 'body', default_value='')
      body = body.strip()

      try:
        body_structure = self._KEY_VALUE_DICT.parseString(body)

        process_identifier = self._GetValueFromStructure(
            body_structure, 'pid')
      except pyparsing.ParseException:
        process_identifier = None

      event_data = SELinuxLogEventData()
      event_data.audit_type = self._GetValueFromStructure(structure, 'type')
      event_data.body = body or None
      event_data.last_written_time = self._ParseTimeElements(
          time_elements_structure)
      event_data.pid = process_identifier

      parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.PosixTimeInMilliseconds: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      seconds, milliseconds = time_elements_structure

      timestamp = (seconds * definitions.MILLISECONDS_PER_SECOND) + milliseconds

      return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'timestamp')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(SELinuxTextPlugin)
