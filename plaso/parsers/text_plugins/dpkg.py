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

  # Date and time values are formatted as:
  # 2009-02-25 11:45:23
  _DATE_TIME = pyparsing.Regex(
      r'(?P<date_time>[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) ')

  _DPKG_STARTUP_TYPE = pyparsing.one_of([
      'archives',
      'packages'])

  _DPKG_STARTUP_COMMAND = pyparsing.one_of([
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

  _DPKG_ACTION = pyparsing.one_of([
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

  _DPKG_CONFFILE_DECISION = pyparsing.one_of([
      'install',
      'keep'])

  _DPKG_CONFFILE_BODY = pyparsing.Combine((
      pyparsing.Literal('conffile') + pyparsing.Word(pyparsing.printables) +
      _DPKG_CONFFILE_DECISION), joinString=' ', adjacent=False)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (_DATE_TIME + pyparsing.MatchFirst([
      _DPKG_STARTUP_BODY, _DPKG_STATUS_BODY, _DPKG_ACTION_BODY,
      _DPKG_CONFFILE_BODY]).set_results_name('body') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  VERIFICATION_LITERALS = [
      ' conffile ', ' configure ', ' disappear ', ' install ', ' purge ',
      ' remove ', ' startup ', ' status ', ' trigproc ', ' upgrade ']

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
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromDateTimeString(time_elements_structure)

      # APT History logs store date and time values in local time.
      date_time.is_local_time = True

      # TODO: remove this after updating dfDateTime not to set the time zone in
      # CopyFromDateTimeString for a time string without time zone information.
      date_time.time_zone_offset = None

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct plugin, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(DpkgTextPlugin)
