# -*- coding: utf-8 -*-
"""This file contains SELinux audit.log file parser.

Information updated 16 january 2013.

An example:

type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

Where msg=audit(1105758604.519:420) contains the number of seconds since
January 1, 1970 00:00:00 UTC and the number of milliseconds after the dot
for example: "seconds: 1105758604, milliseconds: 519".

The number after the timestamp (420 in the example) is a 'serial number'
that can be used to correlate multiple logs generated from the same event.

References:

* http://selinuxproject.org/page/NB_AL
* http://blog.commandlinekungfu.com/2010/08/episode-106-epoch-fail.html
* http://www.redhat.com/promo/summit/2010/presentations/taste_of_training/
    Summit_2010_SELinux.pdf
"""

from __future__ import unicode_literals

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


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


class SELinuxParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for SELinux audit.log files."""

  NAME = 'selinux'
  DESCRIPTION = 'Parser for SELinux audit.log files.'

  _ENCODING = 'utf-8'

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

  LINE_STRUCTURES = [('line', _SELINUX_LOG_LINE)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a structure of tokens derived from a line of a text file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

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
    # TODO: pass line number to offset or remove.
    event_data.offset = 0

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    try:
      structure = self._SELINUX_LOG_LINE.parseString(line)
    except pyparsing.ParseException as exception:
      logger.debug(
          'Unable to parse SELinux audit.log file with error: {0!s}'.format(
              exception))
      return False

    return 'type' in structure and 'msg' in structure


manager.ParsersManager.RegisterParser(SELinuxParser)
