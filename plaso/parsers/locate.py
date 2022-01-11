# -*- coding: utf-8 -*-
"""Parser for locate database (updatedb) files."""

import os

from dfdatetime import posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class LocateDatabaseEvent(events.EventData):
  """Linux locate database (updatedb) event data.

  Attributes:
    paths (list[str]): paths of the locate database (updatedb) entry.
  """

  DATA_TYPE = 'linux:locate'

  def __init__(self):
    """Initializes event data."""
    super(LocateDatabaseEvent, self).__init__(data_type=self.DATA_TYPE)
    self.paths = None


class LocateDatabaseParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for locate database (updatedb) files."""

  NAME = 'locate_database'
  DATA_FORMAT = 'Locate database file (updatedb)'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'locate.yaml')

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\x00mlocate', offset=0)
    return format_specification

  #pylint: disable=unused-argument
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

    directory_header_map = self._GetDataTypeMap('directory_header')
    directory_entry_header_map = self._GetDataTypeMap('directory_entry_header')
    cstring_map = self._GetDataTypeMap('cstring')

    file_size = file_object.get_size()
    while file_offset + 16 < file_size:
      try:
        directory_header, data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, directory_header_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse locate directory header at offset: 0x{0:08x} with '
            'error: {1!s}').format(file_offset, exception))
        return

      file_offset += data_size

      event_data = LocateDatabaseEvent()
      event_data.paths = [directory_header.path]

      timestamp = directory_header.nanoseconds + (
          directory_header.seconds * definitions.NANOSECONDS_PER_SECOND)
      date_time = posix_time.PosixTimeInNanoseconds(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      # TODO: determine why "condition: directory_entry.type != 2" in dtFabric
      # definitions is currently not working and clean up code once fixed.
      directory_entry_type = 0
      while directory_entry_type != 2:
        try:
          directory_entry_header, data_size = self._ReadStructureFromFileObject(
              file_object, file_offset, directory_entry_header_map)
        except (ValueError, errors.ParseError) as exception:
          parser_mediator.ProduceExtractionWarning((
              'unable to parse locate directory entry header at offset: '
              '0x{0:08x} with error: {1!s}').format(file_offset, exception))
          return

        file_offset += data_size

        directory_entry_type = directory_entry_header.type
        if directory_entry_type != 2:
          try:
            directory_entry_path, data_size = self._ReadStructureFromFileObject(
                file_object, file_offset, cstring_map)
          except (ValueError, errors.ParseError) as exception:
            parser_mediator.ProduceExtractionWarning((
                'unable to parse locate directory entry path at offset: '
                '0x{0:08x} with error: {1!s}').format(file_offset, exception))
            return

          event_data.paths.append(directory_entry_path)

          file_offset += data_size


manager.ParsersManager.RegisterParser(LocateDatabaseParser)
