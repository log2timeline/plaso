# -*- coding: utf-8 -*-
"""Parser for Debian package manager log (dpkg.log) files.

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

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class DpkgEventData(events.EventData):
  """Dpkg event data.

  Attributes:
    body (str): body of the log line.
  """

  DATA_TYPE = 'dpkg:line'

  def __init__(self):
    """Initializes event data."""
    super(DpkgEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None


class DpkgParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for Debian package manager log (dpkg.log) files."""

  NAME = 'dpkg'
  DATA_FORMAT = 'Debian package manager log (dpkg.log) file'

  _ENCODING = 'utf-8'

  _DPKG_STARTUP = 'startup'
  _DPKG_STATUS = 'status'
  _DPKG_CONFFILE = 'conffile'

  _DPKG_ACTIONS = [
      'install',
      'upgrade',
      'configure',
      'trigproc',
      'disappear',
      'remove',
      'purge']

  _DPKG_STARTUP_TYPES = [
      'archives',
      'packages']

  _DPKG_STARTUP_COMMANDS = [
      'unpack',
      'install',
      'configure',
      'triggers-only',
      'remove',
      'purge']

  _DPKG_CONFFILE_DECISIONS = [
      'install',
      'keep']

  _DPKG_STARTUP_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_STARTUP) +
      pyparsing.oneOf(_DPKG_STARTUP_TYPES) +
      pyparsing.oneOf(_DPKG_STARTUP_COMMANDS),
      joinString=' ', adjacent=False)

  _DPKG_STATUS_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_STATUS) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables),
      joinString=' ', adjacent=False)

  _DPKG_ACTION_BODY = pyparsing.Combine(
      pyparsing.oneOf(_DPKG_ACTIONS) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables),
      joinString=' ', adjacent=False)

  _DPKG_CONFFILE_BODY = pyparsing.Combine(
      pyparsing.Literal(_DPKG_CONFFILE) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.oneOf(_DPKG_CONFFILE_DECISIONS),
      joinString=' ', adjacent=False)

  _DPKG_LOG_LINE = (
      text_parser.PyparsingConstants.DATE_TIME.setResultsName('date_time') +
      pyparsing.MatchFirst([
          _DPKG_STARTUP_BODY,
          _DPKG_STATUS_BODY,
          _DPKG_ACTION_BODY,
          _DPKG_CONFFILE_BODY]).setResultsName('body'))

  LINE_STRUCTURES = [('line', _DPKG_LOG_LINE)]

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
    if key != 'line':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exists.
    time_elements_structure = structure.get('date_time', None)

    try:
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
          year, month, day_of_month, hours, minutes, seconds))
      date_time.is_local_time = True

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_structure))
      return

    body_text = self._GetValueFromStructure(structure, 'body')
    if not body_text:
      parser_mediator.ProduceExtractionWarning('missing body text')
      return

    event_data = DpkgEventData()
    event_data.body = body_text

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    try:
      structure = self._DPKG_LOG_LINE.parseString(line)
    except pyparsing.ParseException as exception:
      logger.debug(
          'Unable to parse Debian dpkg.log file with error: {0!s}'.format(
              exception))
      return False

    return 'date_time' in structure and 'body' in structure


manager.ParsersManager.RegisterParser(DpkgParser)
