# -*- coding: utf-8 -*-
"""Parser for Linux utmp files."""

import os

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class UtmpEventData(events.EventData):
  """Linux libc6 utmp event data.

  Attributes:
    exit_status (int): exit status.
    hostname (str): hostname or IP address.
    ip_address (str): IP address from the connection.
    offset (int): offset of the utmp record relative to the start of the file,
        from which the event data was extracted.
    pid (int): process identifier (PID).
    terminal_identifier (int): inittab identifier.
    terminal (str): type of terminal.
    type (int): type of login.
    username (str): user name.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'linux:utmp:event'

  def __init__(self):
    """Initializes event data."""
    super(UtmpEventData, self).__init__(data_type=self.DATA_TYPE)
    self.exit_status = None
    self.hostname = None
    self.ip_address = None
    self.offset = None
    self.pid = None
    self.terminal_identifier = None
    self.terminal = None
    self.type = None
    self.username = None
    self.written_time = None


class UtmpParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for Linux libc6 utmp files."""

  NAME = 'utmp'
  DATA_FORMAT = 'Linux libc6 utmp file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'utmp.yaml')

  _EMPTY_IP_ADDRESS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

  _SUPPORTED_TYPES = frozenset(range(0, 10))

  _DEAD_PROCESS_TYPE = 8

  def _ReadEntry(self, parser_mediator, file_object, file_offset):
    """Reads an utmp entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the data relative to the start of
          the file-like object.

    Returns:
      tuple: containing:

        UtmpEventData: event data of the utmp entry read.
        list[str]: warning messages emitted by the parser.

    Raises:
      ParseError: if the entry cannot be parsed.
    """
    entry_map = self._GetDataTypeMap('linux_libc6_utmp_entry')
    warning_strings = []

    try:
      entry, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, entry_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse utmp entry at offset: 0x{0:08x} with error: '
          '{1!s}.').format(file_offset, exception))

    if entry.type not in self._SUPPORTED_TYPES:
      raise errors.ParseError('Unsupported type: {0:d}'.format(entry.type))

    code_page = parser_mediator.GetCodePage()

    try:
      username = entry.username.split(b'\x00')[0]
      username = username.decode(code_page).rstrip()
    except UnicodeDecodeError:
      warning_strings.append('unable to decode username string')
      username = None

    try:
      terminal = entry.terminal.split(b'\x00')[0]
      terminal = terminal.decode(code_page).rstrip()
    except UnicodeDecodeError:
      warning_strings.append('unable to decode terminal string')
      terminal = None

    if terminal == '~':
      terminal = 'system boot'

    try:
      hostname = entry.hostname.split(b'\x00')[0]
      hostname = hostname.decode(code_page).rstrip()
    except UnicodeDecodeError:
      warning_strings.append('unable to decode hostname string')
      hostname = None

    if not hostname or hostname == ':0':
      hostname = 'localhost'

    if entry.ip_address[4:] == self._EMPTY_IP_ADDRESS[4:]:
      ip_address = self._FormatPackedIPv4Address(entry.ip_address[:4])
    else:
      ip_address = self._FormatPackedIPv6Address(entry.ip_address)

    timestamp = entry.microseconds + (
        entry.timestamp * definitions.MICROSECONDS_PER_SECOND)

    # TODO: add termination status.
    event_data = UtmpEventData()
    event_data.hostname = hostname
    event_data.exit_status = entry.exit_status
    event_data.ip_address = ip_address
    event_data.offset = file_offset
    event_data.pid = entry.pid
    event_data.terminal = terminal or None
    event_data.terminal_identifier = entry.terminal_identifier
    event_data.type = entry.type
    event_data.username = username or None
    event_data.written_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)

    return event_data, warning_strings

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an utmp file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_offset = 0

    try:
      event_data, warning_strings = self._ReadEntry(
          parser_mediator, file_object, file_offset)
    except errors.ParseError as exception:
      raise errors.WrongParser(
          'Unable to parse first utmp entry with error: {0!s}'.format(
              exception))

    if not event_data.written_time:
      raise errors.WrongParser(
          'Unable to parse first utmp entry with error: missing written time')

    if not event_data.username and event_data.type != self._DEAD_PROCESS_TYPE:
      raise errors.WrongParser(
          'Unable to parse first utmp entry with error: missing username')

    if warning_strings:
      all_warnings = ', '.join(warning_strings)
      raise errors.WrongParser(
          'Unable to parse first utmp entry with error: {0:s}'.format(
              all_warnings))

    parser_mediator.ProduceEventData(event_data)

    file_offset = file_object.tell()
    file_size = file_object.get_size()

    while file_offset < file_size:
      if parser_mediator.abort:
        break

      try:
        event_data, warning_strings = self._ReadEntry(
            parser_mediator, file_object, file_offset)
      except errors.ParseError:
        # Note that the utmp file can contain trailing data.
        break

      parser_mediator.ProduceEventData(event_data)

      for warning_string in warning_strings:
        parser_mediator.ProduceExtractionWarning(warning_string)

      file_offset = file_object.tell()


manager.ParsersManager.RegisterParser(UtmpParser)
