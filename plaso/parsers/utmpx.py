# -*- coding: utf-8 -*-
"""Parser for utmpx files."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager


class UtmpxMacOSEventData(events.EventData):
  """MacOS utmpx event data.

  Attributes:
    hostname (str): hostname or IP address.
    pid (int): process identifier (PID).
    terminal (str): name of the terminal.
    terminal_identifier (int): inittab identifier.
    type (int): type of login.
    username (str): user name.
  """

  DATA_TYPE = 'mac:utmpx:event'

  def __init__(self):
    """Initializes event data."""
    super(UtmpxMacOSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.hostname = None
    self.pid = None
    self.terminal = None
    self.terminal_identifier = None
    self.type = None
    self.username = None


class UtmpxParser(dtfabric_parser.DtFabricBaseParser):
  """Parser for Mac OS X 10.5 utmpx files."""

  NAME = 'utmpx'
  DESCRIPTION = 'Parser for Mac OS X 10.5 utmpx files.'

  _DEFINITION_FILE = 'utmp.yaml'

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
      tuple: containing:

        int: timestamp, which contains the number of microseconds
            since January 1, 1970, 00:00:00 UTC.
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
      raise errors.UnableToParseFile('Unsupported type: {0:d}'.format(
          entry.type))

    encoding = parser_mediator.codepage or 'utf8'

    try:
      username = entry.username.split(b'\x00')[0]
      username = username.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode username string')
      username = None

    try:
      terminal = entry.terminal.split(b'\x00')[0]
      terminal = terminal.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode terminal string')
      terminal = None

    if terminal == '~':
      terminal = 'system boot'

    try:
      hostname = entry.hostname.split(b'\x00')[0]
      hostname = hostname.decode(encoding)
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to decode hostname string')
      hostname = None

    if not hostname:
      hostname = 'localhost'

    event_data = UtmpxMacOSEventData()
    event_data.hostname = hostname
    event_data.pid = entry.pid
    event_data.offset = file_offset
    event_data.terminal = terminal
    event_data.terminal_identifier = entry.terminal_identifier
    event_data.type = entry.type
    event_data.username = username

    timestamp = entry.microseconds + (
        entry.timestamp * definitions.MICROSECONDS_PER_SECOND)
    return timestamp, event_data

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
      UnableToParseFile: when the file cannot be parsed.
    """
    file_offset = 0

    try:
      timestamp, event_data = self._ReadEntry(
          parser_mediator, file_object, file_offset)
    except errors.ParseError as exception:
      raise errors.UnableToParseFile(
          'Unable to parse utmpx file header with error: {0!s}'.format(
              exception))

    if event_data.username != self._FILE_HEADER_USERNAME:
      raise errors.UnableToParseFile(
          'Unable to parse utmpx file header with error: unsupported username')

    if event_data.type != self._FILE_HEADER_TYPE:
      raise errors.UnableToParseFile(
          'Unable to parse utmp file header with error: unsupported type of '
          'login')

    file_offset = file_object.tell()
    file_size = file_object.get_size()

    while file_offset < file_size:
      if parser_mediator.abort:
        break

      try:
        timestamp, event_data = self._ReadEntry(
            parser_mediator, file_object, file_offset)
      except errors.ParseError as exception:
        break

      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_START)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      file_offset = file_object.tell()


manager.ParsersManager.RegisterParser(UtmpxParser)
