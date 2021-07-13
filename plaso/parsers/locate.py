# -*- coding: utf-8 -*-
"""Parser for locate/updatedb database files."""

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
  """Linux Locate Database event data.

  Attributes:
    folder_path (str): full folder path.
  """

  DATA_TYPE = 'linux:locate'

  def __init__(self):
    """Initializes event data."""
    super(LocateDatabaseEvent, self).__init__(data_type=self.DATA_TYPE)
    self.folder_path = None


class LocateDatabaseFile(dtfabric_helper.DtFabricHelper):
  """Locate database file."""

  _DEFINITION_FILE = os.path.join(
    os.path.dirname(__file__), 'locate.yaml')

  DB_MAGIC = b"\x00mlocate"

  def __init__(self):
    """Initialises a locate database file."""
    super(LocateDatabaseFile, self).__init__()
    self.root_path = None
    self._file_object = None
    self._file_offset = 0

  def Close(self):
    """Closes the file."""
    self._file_object = None
    self._file_offset = 0

  def ParsePaths(self):
    """Retrieves the paths and the last created|modified time

    Yields:
      tuple[str, PosixTimeInNanoSeconds]: path name and the last
        created|modified time

    Raises:
      UnableToParseFile: if the file cannot be parsed
    """
    directory_header_map = self._GetDataTypeMap('directory_header')
    directory_entry_map = self._GetDataTypeMap('directory_entry')
    cstring_map = self._GetDataTypeMap('cstring')

    while True:
      if self._file_object.tell() + 16 > self._file_object.get_size():
        break
      try:
        directory_header, directory_header_size = (
          self._ReadStructureFromFileObject(self._file_object,
            self._file_offset, directory_header_map))
        self._file_offset += directory_header_size
      except (ValueError, errors.ParseError) as exception:
        raise errors.UnableToParseFile(
          'Unable to parse locate directory header with error {0!s}'.format(
            exception))

      directory_timestamp = (directory_header.time_sec *
        definitions.NANOSECONDS_PER_SECOND)
      directory_timestamp += directory_header.time_nsec
      posix_timestamp = posix_time.PosixTimeInNanoseconds(
        timestamp=directory_timestamp)
      yield directory_header.name, posix_timestamp

      # skip over file / subdirectory names as they don't have any timestamps
      while True:
        try:
          directory_entry, directory_entry_size = (
            self._ReadStructureFromFileObject(self._file_object,
              self._file_offset, directory_entry_map))
          self._file_offset += directory_entry_size
          if directory_entry.type == 0x02:
            break

          _, data_size = self._ReadStructureFromFileObject(
            self._file_object, self._file_offset, cstring_map)
          self._file_offset += data_size
        except (ValueError, errors.ParseError) as exception:
          raise errors.UnableToParseFile(
            'Unable to parse locate directory entry with error {0!s}'.format(
              exception))


  def Open(self, file_object):
    """Opens a Locate database file.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      IOError: if the file-like object cannot be read.
      OSError: if the file-like object cannot be read.
      ValueError: if the file-like object is missing.
      UnableToParseFile: if the file cannot be parsed
    """
    if not file_object:
      raise ValueError('Missing file object.')

    self._file_object = file_object

    locate_database_header_map = self._GetDataTypeMap('locate_database_header')

    try:
      locate_database_header, data_size = self._ReadStructureFromFileObject(
        self._file_object, self._file_offset, locate_database_header_map)
      self._file_offset += data_size
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
        'Unable to parse locate database header with error: {0!s}'.format(
          exception))
    if locate_database_header.signature != self.DB_MAGIC:
      raise errors.UnableToParseFile('Invalid file magic')

    cstring_map = self._GetDataTypeMap('cstring')
    try:
      self.root_path, data_size = self._ReadStructureFromFileObject(
        self._file_object, self._file_offset, cstring_map)
      self._file_offset += data_size
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
        'Unable to parse root path with error: {0!s}'.format(
          exception))

    # skip configuration section for now
    self._file_offset += locate_database_header.conf_size


class LocateDatabaseParser(interface.FileObjectParser):
  """Parser for locate/updatedb database files"""

  NAME = 'locate_database'
  DATA_FORMAT = 'Locate Database file'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification

    Returns:
      FormatSpecification: format specifation.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(LocateDatabaseFile.DB_MAGIC, offset=0)
    return format_specification

  #pylint: disable=unused-argument
  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a locate/updatedb database file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): file-like object to be parsed.

    Raises:
      UnableToParseFile: when the file cannot be parsed, this will signal
        the event extractor to apply other parsers.
    """
    locate_file = LocateDatabaseFile()

    try:
      locate_file.Open(file_object)

      for (folder_path, folder_timestamp) in locate_file.ParsePaths():
        event_data = LocateDatabaseEvent()
        event_data.folder_path = folder_path

        event = time_events.DateTimeValuesEvent(
          folder_timestamp, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)
    except Exception as exception:  # pylint: disable=broad-except
      raise errors.UnableToParseFile(
        'unable to parse locate database with error: {0!s}'.format(exception))
    finally:
      locate_file.Close()


manager.ParsersManager.RegisterParser(LocateDatabaseParser)
