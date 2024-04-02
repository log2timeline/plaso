# -*- coding: utf-8 -*-
"""Text parser plugins for TeamViewer log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class TeamViewerApplicationEventData(events.EventData):
  """TeamViewer application log event data.

  Attributes:
    body (str): body of the log entry.
    process_identifier (int): process identifier that generated the log entry.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
  """

  DATA_TYPE = 'teamviewer:application_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerApplicationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.body = None
    self.process_identifier = None
    self.recorded_time = None


class TeamViewerConnectionsIncomingEventData(events.EventData):
  """TeamViewer incoming connection log event data.

  Attributes:
    activity_type (str): Type of the activity, such as RemoteSupport or
        FileTransfer.
    connection_identifier (str): identifier of the connection, contains an UUID.
    display_name (string): The display name of the incoming connection source.
        Usually the computer name or the TeamViewer user name.
    end_time (dfdatetime.DateTimeValues): connection end time in UTC.
    local_account (str): The local user account associated with this activity.
    source_identifier (int): TeamViewer identifier of the incoming connection.
    start_time (dfdatetime.DateTimeValues): connection start time in UTC.
  """

  DATA_TYPE = 'teamviewer:connections_incoming:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerConnectionsIncomingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.activity_type = None
    self.connection_identifier = None
    self.display_name = None
    self.end_time = None
    self.local_account = None
    self.source_identifier = None
    self.start_time = None


class TeamViewerConnectionsOutgoingEventData(events.EventData):
  """TeamViewer outgoing connection log event data.

  Attributes:
    activity_type (str): Type of the activity, such as RemoteSupport or
        FileTransfer.
    connection_identifier (str): identifier of the connection, contains a UUID.
    destination_identifier (int): TeamViewer identifier of the destination.
    end_time (dfdatetime.DateTimeValues): connection end time in UTC.
    local_account (str): The local user account associated
        with this activity.
    start_time (dfdatetime.DateTimeValues): connection start time in UTC.
  """

  DATA_TYPE = 'teamviewer:connections_outgoing:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerConnectionsOutgoingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.activity_type = None
    self.connection_identifier = None
    self.destination_identifier = None
    self.end_time = None
    self.local_account = None
    self.start_time = None


class TeamViewerApplicationLogTextPlugin(
    interface.TextPluginWithLineContinuation):
  """Text parser plugin for TeamViewer application log files."""

  NAME = 'teamviewer_application_log'
  DATA_FORMAT = 'TeamViewer application log file parser.'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _TIMESTAMP = (
      _FOUR_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _THREE_DIGITS)

  _LOG_LINE = (
      _TIMESTAMP.set_results_name('timestamp') +
      pyparsing.Word(pyparsing.nums).set_parse_action(
          lambda tokens: int(tokens[0], 10)).set_results_name(
              'process_identifier') +
      # Field with unknown purpose.
      pyparsing.Suppress(pyparsing.Word(pyparsing.nums)) +
      # Field with unknown purpose.
      pyparsing.Suppress(pyparsing.Word(pyparsing.alphanums + '!')) +
      pyparsing.restOfLine().set_results_name('body') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VERIFICATION_GRAMMAR = _LOG_LINE

  _LINE_STRUCTURES = [('log_line', _LOG_LINE) ]

  def __init__(self):
    """Initializes a text parser plugin."""
    super(TeamViewerApplicationLogTextPlugin, self).__init__()
    self._body_lines = None
    self._event_data = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      self._event_data.body = ''.join(self._body_lines)
      self._body_lines = None

      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

  def _ParseLogLine(self, structure):
    """Parses a log line.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'timestamp')

    event_data = TeamViewerApplicationEventData()
    event_data.process_identifier = self._GetValueFromStructure(
         structure, 'process_identifier')
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)

    body = self._GetValueFromStructure(structure, 'body').strip()

    self._body_lines = [body]
    self._event_data = event_data

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
    if key == '_line_continuation':
      body = structure.strip()
      self._body_lines.append(body)

    else:
      if self._event_data:
        self._event_data.body = ''.join(self._body_lines)
        parser_mediator.ProduceEventData(self._event_data)

      self._ParseLogLine(structure)

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
      year, month, day, hours, minutes, seconds, milliseconds = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day, hours, minutes, seconds, milliseconds)

      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

  def _ResetState(self):
    """Resets stored values."""
    self._body_lines = None
    self._event_data = None

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
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'timestamp')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


class TeamViewerConnectionsOutgoingLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for TeamViewer connections.txt log files."""

  NAME = 'teamviewer_connections_outgoing'
  DATA_FORMAT = 'TeamViewer connections.txt log file'

  _TEAMVIEWER_ID = pyparsing.Word(
      pyparsing.nums, min=8, max=11).set_parse_action(
          lambda tokens: int(tokens[0], 10))

  _NAME = pyparsing.Word(pyparsing.alphanums + '-' + '.' + '_')
  _GUID = pyparsing.Word(pyparsing.hexnums + '{' + '}' + '-')

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _DATE = (
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _FOUR_DIGITS)

  _TIME = (
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS)

  _DATE_TIME = _DATE + _TIME

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _TEAMVIEWER_ID.set_results_name('source_identifier') +
      _DATE_TIME.set_results_name('session_start_timestamp') +
      _DATE_TIME.set_results_name('session_end_timestamp') +
      _NAME.set_results_name('local_account') +
      pyparsing.Word(pyparsing.alphanums).set_results_name('activity_type') +
      _GUID.set_results_name('connection_identifier') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VERIFICATION_GRAMMAR = _LOG_LINE

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

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
    start_time_elements = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    end_time_elements = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    event_data = TeamViewerConnectionsOutgoingEventData()
    event_data.activity_type = self._GetValueFromStructure(
        structure, 'activity_type')
    event_data.connection_identifier = self._GetValueFromStructure(
        structure, 'connection_identifier')
    event_data.end_time = self._ParseTimeElements(end_time_elements)
    event_data.local_account = self._GetValueFromStructure(
        structure, 'local_account')
    event_data.destination_identifier = self._GetValueFromStructure(
        structure, 'source_identifier')
    event_data.start_time = self._ParseTimeElements(start_time_elements)

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
      day_of_month, month, year, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple, time_zone_offset=0)
      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

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
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    start_time_elements = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    end_time_elements = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    try:
      self._ParseTimeElements(start_time_elements)
      self._ParseTimeElements(end_time_elements)
    except errors.ParseError:
      return False

    return True


class TeamViewerConnectionsIncomingLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for TeamViewer connections_incoming.txt ."""

  NAME = 'teamviewer_connections_incoming'
  DATA_FORMAT = 'TeamViewer connections_incoming.txt log file'

  _TEAMVIEWER_ID = pyparsing.Word(
      pyparsing.nums, min=8, max=11).set_parse_action(
          lambda tokens: int(tokens[0], 10))

  _NAME = pyparsing.Word(pyparsing.alphanums + '-' + '.' + '_')
  _GUID = pyparsing.Word(pyparsing.hexnums + '{' + '}' + '-')

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _DATE = (
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _FOUR_DIGITS)

  _TIME = (
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS)

  _DATE_TIME = _DATE + _TIME

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _TEAMVIEWER_ID.set_results_name('source_identifier') +
      _NAME.set_results_name('display_name') +
      _DATE_TIME.set_results_name('session_start_timestamp') +
      _DATE_TIME.set_results_name('session_end_timestamp') +
      _NAME.set_results_name('local_account') +
      pyparsing.Word(pyparsing.alphanums).set_results_name('activity_type') +
      _GUID.set_results_name('connection_identifier') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VERIFICATION_GRAMMAR = _LOG_LINE

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

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
    start_time_elements = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    end_time_elements = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    event_data = TeamViewerConnectionsIncomingEventData()
    event_data.activity_type = self._GetValueFromStructure(
        structure, 'activity_type')
    event_data.connection_identifier = self._GetValueFromStructure(
        structure, 'connection_identifier')
    event_data.display_name = self._GetValueFromStructure(
        structure, 'display_name')
    event_data.end_time = self._ParseTimeElements(end_time_elements)
    event_data.local_account = self._GetValueFromStructure(
        structure, 'local_account')
    event_data.source_identifier = self._GetValueFromStructure(
        structure, 'source_identifier')
    event_data.start_time = self._ParseTimeElements(start_time_elements)

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
      day_of_month, month, year, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple, time_zone_offset=0)
      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

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
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    start_time_elements = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    end_time_elements = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    try:
      self._ParseTimeElements(start_time_elements)
      self._ParseTimeElements(end_time_elements)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugins([
    TeamViewerApplicationLogTextPlugin,
    TeamViewerConnectionsIncomingLogTextPlugin,
    TeamViewerConnectionsOutgoingLogTextPlugin])
