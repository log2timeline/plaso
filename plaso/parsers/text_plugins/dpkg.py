# -*- coding: utf-8 -*-
"""Text parser plugin for Debian package manager log (dpkg.log) files.

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
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class DpkgEventData(events.EventData):
  """Dpkg event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    body (str): body of the log line.
  """

  DATA_TYPE = 'linux:dpkg_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(DpkgEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.body = None


class DpkgTextPlugin(interface.TextPlugin):
  """Text parser plugin for Debian package manager log (dpkg.log) files."""

  NAME = 'dpkg'
  DATA_FORMAT = 'Debian package manager log (dpkg.log) file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS).setResultsName('date_time')

  _DPKG_STARTUP_TYPE = pyparsing.oneOf([
      'archives',
      'packages'])

  _DPKG_STARTUP_COMMAND = pyparsing.oneOf([
      'unpack',
      'install',
      'configure',
      'triggers-only',
      'remove',
      'purge'])

  _DPKG_STARTUP_BODY = pyparsing.Combine((
      pyparsing.Literal('startup') + _DPKG_STARTUP_TYPE +
      _DPKG_STARTUP_COMMAND), joinString=' ', adjacent=False)

  _DPKG_STATUS_BODY = pyparsing.Combine((
      pyparsing.Literal('status') + pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables)), joinString=' ', adjacent=False)

  _DPKG_ACTION = pyparsing.oneOf([
      'install',
      'upgrade',
      'configure',
      'trigproc',
      'disappear',
      'remove',
      'purge'])

  _DPKG_ACTION_BODY = pyparsing.Combine((
      _DPKG_ACTION + pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables)), joinString=' ', adjacent=False)

  _DPKG_CONFFILE_DECISION = pyparsing.oneOf([
      'install',
      'keep'])

  _DPKG_CONFFILE_BODY = pyparsing.Combine((
      pyparsing.Literal('conffile') + pyparsing.Word(pyparsing.printables) +
      _DPKG_CONFFILE_DECISION), joinString=' ', adjacent=False)

  _DPKG_LOG_LINE = (_DATE_TIME + pyparsing.MatchFirst([
      _DPKG_STARTUP_BODY, _DPKG_STATUS_BODY, _DPKG_ACTION_BODY,
      _DPKG_CONFFILE_BODY]).setResultsName('body'))

  _LINE_STRUCTURES = [('line', _DPKG_LOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = DpkgEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.body = self._GetValueFromStructure(structure, 'body')

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string
      # when named token does not exists.
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
          year, month, day_of_month, hours, minutes, seconds))
      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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
      parsed_structure = self._DPKG_LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    if 'body' not in parsed_structure:
      return False

    time_elements_structure = self._GetValueFromStructure(
        parsed_structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.SingleLineTextParser.RegisterPlugin(DpkgTextPlugin)
