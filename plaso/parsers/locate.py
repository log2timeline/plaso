# -*- coding: utf-8 -*-
"""Parser for locate database (updatedb) files."""

import os

from dfdatetime import posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class LocateDatabaseEvent(events.EventData):
  """Linux locate database (updatedb) event data.

  Attributes:
    entries (list[str]): contents of the locate database (updatedb) entry.
    path (str): path of the locate database (updatedb) entry.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'linux:locate_database:entry'

  def __init__(self):
    """Initializes event data."""
    super(LocateDatabaseEvent, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.path = None
    self.written_time = None


class LocateDatabaseParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for locate database (updatedb) files."""

  NAME = 'locate_database'
  DATA_FORMAT = 'Locate database file (updatedb)'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'locate.yaml')

  def __init__(self):
    """Initializes a locate database (updatedb) file parser."""
    super(LocateDatabaseParser, self).__init__()
    self._cstring_map = self._GetDataTypeMap('cstring')
    self._directory_entry_header_map = self._GetDataTypeMap(
        'directory_entry_header')
    self._directory_header_map = self._GetDataTypeMap('directory_header')

  def _ParseDirectoryEntry(self, file_object, file_offset):
    """Parses a locate database (updatedb) directory entry.

    Args:
      file_object (dfvfs.FileIO): file-like object to be parsed.
      file_offset (int): offset of the directory entry relative to the start of
          the file.

    Returns:
      tuple[list[str], int]: names of sub directory entries and total number of
          bytes read.
    """
    sub_entry_names = []
    total_data_size = 0

    # TODO: determine why "condition: directory_entry.type != 2" in dtFabric
    # definitions is currently not working and clean up code once fixed.
    directory_entry_type = 0
    while directory_entry_type != 2:
      directory_entry_header, data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, self._directory_entry_header_map)

      file_offset += data_size
      total_data_size += data_size

      directory_entry_type = directory_entry_header.type
      if directory_entry_type != 2:
        directory_entry_path, data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, self._cstring_map)

        sub_entry_names.append(directory_entry_path)

        file_offset += data_size
        total_data_size += data_size

    return sub_entry_names, total_data_size

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\x00mlocate', offset=0)
    return format_specification

  # pylint: disable=unused-argument
  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a locate database (updatedb) file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): file-like object to be parsed.

    Raises:
      WrongParser: when the file cannot be parsed, this will signal
          the event extractor to apply other parsers.
    """
    locate_database_header_map = self._GetDataTypeMap('locate_database_header')

    try:
      locate_database_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, locate_database_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse locate database header with error: {0!s}'.format(
              exception))

    # Skip configuration block for now.
    file_offset += locate_database_header.configuration_block_size

    file_size = file_object.get_size()
    while file_offset + 16 < file_size:
      try:
        directory_header, data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, self._directory_header_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse locate directory header at offset: 0x{0:08x} with '
            'error: {1!s}').format(file_offset, exception))
        return

      file_offset += data_size

      timestamp = directory_header.nanoseconds + (
          directory_header.seconds * definitions.NANOSECONDS_PER_SECOND)

      try:
        entries, data_size = self._ParseDirectoryEntry(
            file_object, file_offset)

        file_offset += data_size

      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse directory entry at offset: 0x{0:08x} with '
            'error: {1!s}').format(file_offset, exception))
        return

      event_data = LocateDatabaseEvent()
      event_data.entries = entries or None
      event_data.path = directory_header.path
      event_data.written_time = posix_time.PosixTimeInNanoseconds(
          timestamp=timestamp)

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(LocateDatabaseParser)
