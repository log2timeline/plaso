# -*- coding: utf-8 -*-
"""Parser for MacOS utmpx files."""

import os

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class UtmpxMacOSEventData(events.EventData):
  """MacOS utmpx event data.

  Attributes:
    hostname (str): hostname or IP address.
    offset (int): offset of the utmpx record relative to the start of the file,
        from which the event data was extracted.
    pid (int): process identifier (PID).
    terminal (str): name of the terminal.
    terminal_identifier (int): inittab identifier.
    type (int): type of login.
    username (str): user name.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'macos:utmpx:entry'

  def __init__(self):
    """Initializes event data."""
    super(UtmpxMacOSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.hostname = None
    self.offset = None
    self.pid = None
    self.terminal = None
    self.terminal_identifier = None
    self.type = None
    self.username = None
    self.written_time = None


class UtmpxParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for Mac OS X 10.5 utmpx files."""

  NAME = 'utmpx'
  DATA_FORMAT = 'Mac OS X 10.5 utmpx file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'utmp.yaml')

  _SUPPORTED_TYPES = frozenset(range(0, 12))

  _FILE_HEADER_USERNAME = 'utmpx-1.00'
  _FILE_HEADER_TYPE = 10

  def _ReadEntry(self, parser_mediator, file_object, file_offset):
    """Reads an utmpx entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the data relative from the start of
          the file-like object.

    Returns:
      UtmpxMacOSEventData: event data of the utmpx entry read.

    Raises:
      ParseError: if the entry cannot be parsed.
    """
    entry_map = self._GetDataTypeMap('macosx_utmpx_entry')

    try:
      entry, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, entry_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse utmpx entry at offset: 0x{0:08x} with error: '
          '{1!s}.').format(file_offset, exception))

    if entry.type not in self._SUPPORTED_TYPES:
      raise errors.ParseError('Unsupported type: {0:d}'.format(entry.type))

    code_page = parser_mediator.GetCodePage()

    try:
      username = entry.username.split(b'\x00')[0]
      username = username.decode(code_page).rstrip()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode username string')
      username = None

    try:
      terminal = entry.terminal.split(b'\x00')[0]
      terminal = terminal.decode(code_page).rstrip()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode terminal string')
      terminal = None

    if terminal == '~':
      terminal = 'system boot'

    try:
      hostname = entry.hostname.split(b'\x00')[0]
      hostname = hostname.decode(code_page).rstrip()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode hostname string')
      hostname = None

    if not hostname:
      hostname = 'localhost'

    timestamp = entry.microseconds + (
        entry.timestamp * definitions.MICROSECONDS_PER_SECOND)

    event_data = UtmpxMacOSEventData()
    event_data.hostname = hostname
    event_data.pid = entry.pid
    event_data.offset = file_offset
    event_data.terminal = terminal or None
    event_data.terminal_identifier = entry.terminal_identifier
    event_data.type = entry.type
    event_data.username = username or None
    event_data.written_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)

    return event_data

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'utmpx-1.00\x00', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an UTMPX file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_offset = 0

    try:
      event_data = self._ReadEntry(parser_mediator, file_object, file_offset)
    except errors.ParseError as exception:
      raise errors.WrongParser(
          'Unable to parse utmpx file header with error: {0!s}'.format(
              exception))

    if event_data.username != self._FILE_HEADER_USERNAME:
      raise errors.WrongParser(
          'Unable to parse utmpx file header with error: unsupported username')

    if event_data.type != self._FILE_HEADER_TYPE:
      raise errors.WrongParser(
          'Unable to parse utmp file header with error: unsupported type of '
          'login')

    file_offset = file_object.tell()
    file_size = file_object.get_size()

    while file_offset < file_size:
      if parser_mediator.abort:
        break

      try:
        event_data = self._ReadEntry(parser_mediator, file_object, file_offset)
      except errors.ParseError:
        break

      parser_mediator.ProduceEventData(event_data)

      file_offset = file_object.tell()


manager.ParsersManager.RegisterParser(UtmpxParser)
