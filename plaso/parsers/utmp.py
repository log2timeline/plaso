# -*- coding: utf-8 -*-
"""Parser for Linux UTMP files."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager


class UtmpEventData(events.EventData):
  """UTMP event data.

  Attributes:
    computer_name (str): name of the computer.
    exit_status (int): exit status.
    ip_address (str): IP address from the connection.
    pid (int): process identifier (PID).
    terminal (str): type of terminal.
    terminal_identifier (int): inittab identifier.
    type (int): type of login.
    username (str): user name.
  """

  DATA_TYPE = 'linux:utmp:event'

  def __init__(self):
    """Initializes event data."""
    super(UtmpEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.exit_status = None
    self.ip_address = None
    self.pid = None
    self.terminal = None
    self.terminal_identifier = None
    self.type = None
    self.username = None


class UtmpParser(dtfabric_parser.DtFabricBaseParser):
  """Parser for Linux/Unix UTMP files."""

  NAME = 'utmp'
  DESCRIPTION = 'Parser for Linux/Unix UTMP files.'

  _DEFINITION_FILE = 'utmp.yaml'

  _EMPTY_IP_ADDRESS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

  _SUPPORTED_TYPES = frozenset(range(0, 10))

  def _ReadEntry(self, parser_mediator, file_object, file_offset):
    """Reads an UTMP entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the data relative from the start of
          the file-like object.

    Returns:
      tuple: contains:

        int: timestamp, which contains the number of microseconds
            since January 1, 1970, 00:00:00 UTC.
        UtmpEventData: event data of the UTMP entry read.

    Raises:
      ParseError: if the entry cannot be parsed.
    """
    entry_map = self._GetDataTypeMap('utmp_entry')

    try:
      entry, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, entry_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse UTMP entry at offset: 0x{0:08x} with error: '
          '{1!s}.').format(file_offset, exception))

    if entry.type not in self._SUPPORTED_TYPES:
      raise errors.UnableToParseFile('Unsupported type: {0:d}'.format(
          entry.type))

    encoding = parser_mediator.codepage or 'utf8'

    try:
      username = entry.username.rstrip(b'\x00')
      username = username.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionError('unable to decode username string')
      username = None

    try:
      terminal = entry.terminal.rstrip(b'\x00')
      terminal = terminal.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionError('unable to decode terminal string')
      terminal = None

    if terminal == '~':
      terminal = 'system boot'

    try:
      hostname = entry.hostname.rstrip(b'\x00')
      hostname = hostname.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionError('unable to decode hostname string')
      hostname = None

    if not hostname or hostname == ':0':
      hostname = 'localhost'

    if entry.ip_address[4:] == self._EMPTY_IP_ADDRESS[4:]:
      ip_address = self._FormatPackedIPv4Address(entry.ip_address[:4])
    else:
      ip_address = self._FormatPackedIPv6Address(entry.ip_address)

    # TODO: add termination status.
    # TODO: rename event data attributes to match data definition.
    event_data = UtmpEventData()
    event_data.computer_name = hostname
    event_data.exit_status = entry.exit_status
    event_data.ip_address = ip_address
    event_data.pid = entry.pid
    event_data.terminal = terminal
    event_data.terminal_identifier = entry.terminal_identifier
    event_data.type = entry.type
    event_data.username = username

    timestamp = entry.microseconds + (
        entry.timestamp * definitions.MICROSECONDS_PER_SECOND)
    return timestamp, event_data

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an UTMP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_offset = 0

    try:
      timestamp, event_data = self._ReadEntry(
          parser_mediator, file_object, file_offset)
    except errors.ParseError as exception:
      raise errors.UnableToParseFile(
          'Unable to parse UTMP header with error: {0!s}'.format(exception))

    if not event_data.username:
      raise errors.UnableToParseFile(
          'Unable to parse UTMP header with error: missing username')

    if not timestamp:
      raise errors.UnableToParseFile(
          'Unable to parse UTMP header with error: missing timestamp')

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    file_offset = file_object.tell()
    file_size = file_object.get_size()

    while file_offset < file_size:
      if parser_mediator.abort:
        break

      try:
        timestamp, event_data = self._ReadEntry(
            parser_mediator, file_object, file_offset)
      except errors.ParseError as exception:
        # Note that the utmp file can contain trailing data.
        break

      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_START)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      file_offset = file_object.tell()


manager.ParsersManager.RegisterParser(UtmpParser)
