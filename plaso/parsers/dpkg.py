# -*- coding: utf-8 -*-
"""This file contains the Debian dpkg.log file parser.

Information updated 02 September 2016.

An example:

2016-08-03 15:25:53 install base-passwd:amd64 <none> 3.5.33

Log messages are of the form:

YYYY-MM-DD HH:MM:SS startup type command
Where type is:
    archives (with a command of unpack or install)
    packages (with a command of configure, triggers-only, remove or purge)

YYYY-MM-DD HH:MM:SS status state pkg installed-version

YYYY-MM-DD HH:MM:SS action pkg installed-version available-version
Where action is:
    install, upgrade, configure, trigproc, disappear, remove or purge.

YYYY-MM-DD HH:MM:SS conffile filename decision
Where decision is install or keep.
"""

import logging

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class DpkgEventData(events.EventData):
  """Dpkg event data.

  Attributes:
    body (str): body of the log line.
  """

  DATA_TYPE = u'dpkg:line'

  def __init__(self):
    """Initializes event data."""
    super(DpkgEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None


class DpkgParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for Debian dpkg.log files."""

  NAME = u'dpkg'
  DESCRIPTION = u'Parser for Debian dpkg.log files.'

  _DPKG_STARTUP = u'startup'
  _DPKG_STATUS = u'status'
  _DPKG_CONFFILE = u'conffile'

  _DPKG_ACTIONS = [
      u'install',
      u'upgrade',
      u'configure',
      u'trigproc',
      u'disappear',
      u'remove',
      u'purge']

  _DPKG_STARTUP_TYPES = [
      u'archives',
      u'packages']

  _DPKG_STARTUP_COMMANDS = [
      u'unpack',
      u'install',
      u'configure',
      u'triggers-only',
      u'remove',
      u'purge']

  _DPKG_CONFFILE_DECISIONS = [
      u'install',
      u'keep']

  _DPKG_STARTUP_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_STARTUP) +
      pyparsing.oneOf(_DPKG_STARTUP_TYPES) +
      pyparsing.oneOf(_DPKG_STARTUP_COMMANDS),
      joinString=u' ', adjacent=False)

  _DPKG_STATUS_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_STATUS) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables),
      joinString=u' ', adjacent=False)

  _DPKG_ACTION_BODY = pyparsing.Combine(
      pyparsing.oneOf(_DPKG_ACTIONS) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables),
      joinString=u' ', adjacent=False)

  _DPKG_CONFFILE_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_CONFFILE) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.oneOf(_DPKG_CONFFILE_DECISIONS),
      joinString=u' ', adjacent=False)

  _DPKG_LOG_LINE = (
      text_parser.PyparsingConstants.DATE_TIME.setResultsName(u'date_time') +
      pyparsing.MatchFirst([
          _DPKG_STARTUP_BODY,
          _DPKG_STATUS_BODY,
          _DPKG_ACTION_BODY,
          _DPKG_CONFFILE_BODY]).setResultsName(u'body'))

  LINE_STRUCTURES = [(u'line', _DPKG_LOG_LINE)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a structure of tokens derived from a line of a text file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != u'line':
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=structure.date_time)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(structure.date_time))
      return

    body_text = structure.body
    if not body_text:
      parser_mediator.ProduceExtractionError(
          u'invalid body {0:s}'.format(structure.body))
      return

    event_data = DpkgEventData()
    event_data.body = body_text

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      line (bytes): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    try:
      structure = self._DPKG_LOG_LINE.parseString(line)
    except pyparsing.ParseException as exception:
      logging.debug(
          u'Unable to parse Debian dpkg.log file with error: {0:s}'.format(
              exception))
      return False

    return (
        u'date_time' in structure and u'body' in structure)


manager.ParsersManager.RegisterParser(DpkgParser)
