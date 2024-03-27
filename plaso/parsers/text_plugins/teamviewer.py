# -*- coding: utf-8 -*-
"""Text parser plugins for TeamViewer application log, outgoing connections log
and incoming connections logs."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class TeamViewerConnectionsIncomingEventData(events.EventData):
  """TeamViewer incoming connection log event data.

  Attributes:
    activity_type (str): Type of the activity
        (e.g. RemoteSupport, FileTransfer).
    connection_guid (str): The GUID associated with the connection.
    display_name (string): The display name of the incoming connection
        source. Usually the computer name or the TeamViewer user name.
    local_account (str): The local user account associated
        with this activity.
    session_end_timestamp (dfdatetime.DateTimeValues): End time
        of the connection (UTC).
    session_start_timestamp (dfdatetime.DateTimeValues): Start time
        of the connection (UTC).
    source_teamviewer_id (int): The TeamViewer ID of
        the incoming connection.
  """

  DATA_TYPE = 'teamviewer:connections_incoming:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerConnectionsIncomingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.activity_type = None
    self.connection_guid = None
    self.display_name = None
    self.local_account = None
    self.session_end_timestamp = None
    self.session_start_timestamp = None
    self.source_teamviewer_id = None


class TeamViewerConnectionsOutgoingEventData(events.EventData):
  """TeamViewer outgoing connection log event data.

  Attributes:
    activity_type (str): Type of the activity
        (e.g. RemoteSupport, FileTransfer).
    connection_guid (str): The GUID associated with the connection.
    destination_teamviewer_id (int): The TeamViewer ID of the destination.
    local_account (str): The local user account associated
        with this activity.
    session_end_timestamp (dfdatetime.DateTimeValues): End time
        of the connection (UTC).
    session_start_timestamp (dfdatetime.DateTimeValues): Start time
        of the connection (UTC).
  """

  DATA_TYPE = 'teamviewer:connections_outgoing:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerConnectionsOutgoingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.activity_type = None
    self.connection_guid = None
    self.destination_teamviewer_id = None
    self.local_account = None
    self.session_end_timestamp = None
    self.session_start_timestamp = None


class TeamViewerApplicationEventData(events.EventData):
  """TeamViewer application log event data.

  Attributes:
      message (str): the log message.
      process_id (int): the process ID that generated the log entry.
      timestamp (dfdatetime.DateTimeValues): the event timestamp.
  """

  DATA_TYPE = 'teamviewer:application_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(TeamViewerApplicationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.message = None
    self.process_id = None
    self.timestamp = None


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
      _THREE_DIGITS
  )

  _LOG_LINE = (
      _TIMESTAMP.set_results_name('timestamp') +
      pyparsing.Word(pyparsing.nums).set_parse_action(
          lambda tokens: int(tokens[0], 10)
      ).set_results_name('process_id') +
      pyparsing.Suppress(pyparsing.Word(pyparsing.nums)) +  # unknown
      pyparsing.Suppress(pyparsing.Word(pyparsing.alphanums + '!')) +  # unknown
      pyparsing.restOfLine().set_results_name('message') +
      pyparsing.Suppress(pyparsing.LineEnd())
  )

  VERIFICATION_GRAMMAR = _LOG_LINE
  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE)
  ]

  def __init__(self):
    """Initializes a text parser plugin."""
    super(TeamViewerApplicationLogTextPlugin, self).__init__()
    self._detail_lines = None
    self._event_data = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      self._event_data.message = ''.join(self._detail_lines)
      self._detail_lines = None

      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

  def _ParseLogLine(self, structure):
    """Parses a log line.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'timestamp'
    )

    event_data = TeamViewerApplicationEventData()
    event_data.timestamp = self._ParseTimeElements(time_elements_structure)
    event_data.process_id = self._GetValueFromStructure(structure, 'process_id')
    message = self._GetValueFromStructure(
        structure, 'message').strip()

    self._event_data = event_data
    self._detail_lines = [message]

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
      detail = structure.strip()
      self._detail_lines.append(detail)
    else:
      if self._event_data:
        self._event_data.message = ''.join(self._detail_lines)
        parser_mediator.ProduceEventData(self._event_data)

      self._ParseLogLine(structure)

  def _ResetState(self):
    """Resets stored values."""
    self._detail_lines = None
    self._event_data = None

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
      (year, month, day, hours, minutes,
          seconds, fractions_of_second) = time_elements_structure
      microseconds = fractions_of_second * 1000
      time_elements_tuple = (year, month, day, hours, minutes,
          seconds, microseconds)
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple
      )
      return date_time
    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

  _TEAMVIEWER_ID = pyparsing.Word(pyparsing.nums, min=8, max=11
      ).set_parse_action(lambda tokens: int(tokens[0], 10))

  _NAME = (
    pyparsing.Word(pyparsing.alphanums + '-' + '.' + '_'))
  _GUID = (
    pyparsing.Word(pyparsing.hexnums + '{' + '}' + '-')
  )

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
    lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
    lambda tokens: int(tokens[0], 10))

  _DATE = (_TWO_DIGITS +
          pyparsing.Suppress('-') + _TWO_DIGITS +
          pyparsing.Suppress('-') + _FOUR_DIGITS)

  _TIME = (_TWO_DIGITS +
          pyparsing.Suppress(':') + _TWO_DIGITS +
          pyparsing.Suppress(':') + _TWO_DIGITS)

  _DATE_TIME = _DATE + _TIME

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _TEAMVIEWER_ID.set_results_name('source_teamviewer_id') +
      _DATE_TIME.set_results_name('session_start_timestamp') +
      _DATE_TIME.set_results_name('session_end_timestamp') +
      _NAME.set_results_name('local_account') +
      pyparsing.Word(pyparsing.alphanums).set_results_name('activity_type') +
      _GUID.set_results_name('connection_guid') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VERIFICATION_GRAMMAR = _LOG_LINE
  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE)
  ]

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
    time_elements_structure_start = self._GetValueFromStructure(
        structure, 'session_start_timestamp'
    )
    time_elements_structure_end = self._GetValueFromStructure(
        structure, 'session_end_timestamp'
    )

    event_data = TeamViewerConnectionsOutgoingEventData()
    event_data.destination_teamviewer_id = self._GetValueFromStructure(
        structure, 'source_teamviewer_id')
    event_data.session_start_timestamp = self._ParseTimeElements(
        time_elements_structure_start)
    event_data.session_end_timestamp = self._ParseTimeElements(
        time_elements_structure_end)
    event_data.local_account = self._GetValueFromStructure(
        structure, 'local_account')
    event_data.activity_type = self._GetValueFromStructure(
        structure, 'activity_type')
    event_data.connection_guid = self._GetValueFromStructure(
        structure, 'connection_guid')


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
      (day_of_month, month, year,
          hours, minutes, seconds) = time_elements_structure
      time_elements_tuple = (year, month, day_of_month,
          hours, minutes, seconds)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=0  # timestamp is UTC
      )
      return date_time
    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

    time_elements_structure_start = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    time_elements_structure_end = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    try:
      self._ParseTimeElements(time_elements_structure_start)
      self._ParseTimeElements(time_elements_structure_end)
    except errors.ParseError:
      return False

    return True

class TeamViewerConnectionsIncomingLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for TeamViewer connections_incoming.txt ."""
  NAME = 'teamviewer_connections_incoming'
  DATA_FORMAT = 'TeamViewer connections_incoming.txt log file'

  _TEAMVIEWER_ID = pyparsing.Word(pyparsing.nums, min=8, max=11
      ).set_parse_action(lambda tokens: int(tokens[0], 10))

  _NAME = (
    pyparsing.Word(pyparsing.alphanums + '-' + '.' + '_'))
  _GUID = (
      pyparsing.Word(pyparsing.hexnums + '{' + '}' + '-')
  )

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
    lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
    lambda tokens: int(tokens[0], 10))

  _DATE = (_TWO_DIGITS +
          pyparsing.Suppress('-') + _TWO_DIGITS +
          pyparsing.Suppress('-') + _FOUR_DIGITS)

  _TIME = (_TWO_DIGITS +
          pyparsing.Suppress(':') + _TWO_DIGITS +
          pyparsing.Suppress(':') + _TWO_DIGITS)

  _DATE_TIME = _DATE + _TIME

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _TEAMVIEWER_ID.set_results_name('source_teamviewer_id') +
      _NAME.set_results_name('display_name') +
      _DATE_TIME.set_results_name('session_start_timestamp') +
      _DATE_TIME.set_results_name('session_end_timestamp') +
      _NAME.set_results_name('local_account') +
      pyparsing.Word(pyparsing.alphanums).set_results_name('activity_type') +
      _GUID.set_results_name('connection_guid') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VERIFICATION_GRAMMAR = _LOG_LINE
  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE)
  ]

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
    time_elements_structure_start = self._GetValueFromStructure(
        structure, 'session_start_timestamp'
    )
    time_elements_structure_end = self._GetValueFromStructure(
        structure, 'session_end_timestamp'
    )

    event_data = TeamViewerConnectionsIncomingEventData()
    event_data.source_teamviewer_id = self._GetValueFromStructure(
        structure, 'source_teamviewer_id')
    event_data.display_name = self._GetValueFromStructure(
        structure, 'display_name')
    event_data.session_start_timestamp = self._ParseTimeElements(
        time_elements_structure_start)
    event_data.session_end_timestamp = self._ParseTimeElements(
        time_elements_structure_end)
    event_data.local_account = self._GetValueFromStructure(
        structure, 'local_account')
    event_data.activity_type = self._GetValueFromStructure(
        structure, 'activity_type')
    event_data.connection_guid = self._GetValueFromStructure(
        structure, 'connection_guid')


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
      (day_of_month, month, year,
          hours, minutes, seconds) = time_elements_structure
      time_elements_tuple = (year, month, day_of_month,
          hours, minutes, seconds)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=0  # timestamp is UTC
      )
      return date_time
    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

    time_elements_structure_start = self._GetValueFromStructure(
        structure, 'session_start_timestamp')
    time_elements_structure_end = self._GetValueFromStructure(
        structure, 'session_end_timestamp')

    try:
      self._ParseTimeElements(time_elements_structure_start)
      self._ParseTimeElements(time_elements_structure_end)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(
    TeamViewerApplicationLogTextPlugin)
text_parser.TextLogParser.RegisterPlugin(
    TeamViewerConnectionsIncomingLogTextPlugin)
text_parser.TextLogParser.RegisterPlugin(
    TeamViewerConnectionsOutgoingLogTextPlugin)
