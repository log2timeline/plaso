# -*- coding: utf-8 -*-
"""This file contains SELinux audit.log file parser.

Information updated 16 january 2013.

An example:

type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

Where msg=audit(1105758604.519:420) contains the number of seconds since
January 1, 1970 00:00:00 UTC and the number of milliseconds after the dot e.g.
seconds: 1105758604, milliseconds: 519.

The number after the timestamp (420 in the example) is a 'serial number'
that can be used to correlate multiple logs generated from the same event.

References:

* http://selinuxproject.org/page/NB_AL
* http://blog.commandlinekungfu.com/2010/08/episode-106-epoch-fail.html
* http://www.redhat.com/promo/summit/2010/presentations/
taste_of_training/Summit_2010_SELinux.pdf
"""

import logging

import pyparsing

from plaso.containers import text_events
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxLineEvent(text_events.TextEvent):
  """Convenience class for a SELinux log line event."""

  DATA_TYPE = u'selinux:line'


class SELinuxParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for SELinux audit.log files."""

  NAME = u'selinux'
  DESCRIPTION = u'Parser for SELinux audit.log files.'

  _SELINUX_KEY_VALUE_GROUP = pyparsing.Group(
      pyparsing.Word(pyparsing.alphanums).setResultsName(u'key') +
      pyparsing.Literal(u'=').suppress() + (
          pyparsing.QuotedString(u'"') ^
          pyparsing.Word(pyparsing.printables)).setResultsName(u'value'))

  _SELINUX_KEY_VALUE_DICT = pyparsing.Dict(
      pyparsing.ZeroOrMore(_SELINUX_KEY_VALUE_GROUP))

  _SELINUX_BODY_GROUP = pyparsing.Group(
      pyparsing.Empty().setResultsName(u'key') +
      pyparsing.restOfLine.setResultsName(u'value'))

  _SELINUX_MSG_GROUP = pyparsing.Group(
      pyparsing.Literal(u'msg').setResultsName(u'key') +
      pyparsing.Literal(u'=audit(').suppress() +
      pyparsing.Word(pyparsing.nums).setResultsName(u'seconds') +
      pyparsing.Literal(u'.').suppress() +
      pyparsing.Word(pyparsing.nums).setResultsName(u'milliseconds') +
      pyparsing.Literal(u':').suppress() +
      pyparsing.Word(pyparsing.nums).setResultsName(u'serial') +
      pyparsing.Literal(u'):').suppress())

  _SELINUX_TYPE_GROUP = pyparsing.Group(
      pyparsing.Literal(u'type').setResultsName(u'key') +
      pyparsing.Literal(u'=').suppress() + (
          pyparsing.Word(pyparsing.srange("[A-Z_]")) ^ (
              pyparsing.Literal(u'UNKNOWN[') +
              pyparsing.Word(pyparsing.nums) +
              pyparsing.Literal(u']'))).setResultsName(u'value'))

  _SELINUX_TYPE_AVC_GROUP = pyparsing.Group(
      pyparsing.Literal(u'type').setResultsName(u'key') +
      pyparsing.Literal(u'=').suppress() + (
          pyparsing.Word(u'AVC') ^
          pyparsing.Word(u'USER_AVC')).setResultsName(u'value'))

  # A log line is formatted as: type=TYPE msg=audit([0-9]+\.[0-9]+:[0-9]+): .*
  _SELINUX_LOG_LINE = pyparsing.Dict(
      _SELINUX_TYPE_GROUP +
      _SELINUX_MSG_GROUP +
      _SELINUX_BODY_GROUP)

  LINE_STRUCTURES = [(u'line', _SELINUX_LOG_LINE)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a structure of tokens derived from a line of a text file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    if key != u'line':
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    msg_value = structure.get(u'msg')
    if not msg_value:
      parser_mediator.ProduceExtractionError(u'missing msg value')
      return

    try:
      seconds = int(msg_value[0], 10)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'unsuppored number of seconds in msg value')
      return

    try:
      milliseconds = int(msg_value[1], 10)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'unsuppored number of milliseconds in msg value')
      return

    timestamp = ((seconds * 1000) + milliseconds) * 1000
    body_text = structure[2][0]

    try:
      key_value_dict = self._SELINUX_KEY_VALUE_DICT.parseString(body_text)
    except pyparsing.ParseException:
      key_value_dict = {}

    attributes = {
        u'audit_type': structure.get(u'type'),
        u'body': body_text,
        u'pid': key_value_dict.get(u'pid')
    }

    event_object = SELinuxLineEvent(timestamp, 0, attributes)
    parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      line (bytes): line from a text file.

    Returns:
      bool: True if the line is in the expected format.
    """
    try:
      structure = self._SELINUX_LOG_LINE.parseString(line)
    except pyparsing.ParseException as exception:
      logging.debug(
          u'Unable to parse SELinux audit.log file with error: {0:s}'.format(
              exception))
      return False

    return u'type' in structure and u'msg' in structure


manager.ParsersManager.RegisterParser(SELinuxParser)
