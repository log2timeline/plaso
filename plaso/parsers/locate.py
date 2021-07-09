# -*- coding: utf-8 -*-
"""Parser for locate/updatedb database files."""

import os

from struct import unpack as struct_unpack
from struct import error as struct_error

from dfdatetime import posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
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


class LocateDatabaseFile(object):
  """Locate database file."""

  DB_MAGIC = b"\x00mlocate"

  # header struct format
  _DB_HEADER = ">8sIbb2s"

  # directory struct format
  _DB_DIRECTORY = ">QI4s"

  # Entry Types
  _DBE_NORMAL = 0
  _DBE_DIRECTORY = 1
  _DBE_END = 2

  def __init__(self):
    """Initialises a locate database file."""
    super(LocateDatabaseFile, self).__init__()
    self.root_path = None
    self._file_object = None

  def Close(self):
    """Closes the file."""
    self._file_object.Close()

  def _ParseCString(self):
    """Parse a C-style string from the file object."""
    root_path = [self._file_object.read(1)]
    # if len(root_path) != 1:
    #  raise IOError
    while root_path[-1] != b'\x00':
      c = self._file_object.read(1)
      # if len(c) != 1:
      #  raise IOError
      root_path.append(c)
    return b"".join(root_path[:-1])

  def ParsePaths(self):
    """Retrieves the paths and the last created|modified time

    Yields:
      tuple[str, PosixTimeInNanoSeconds]: path name and the last
        created|modified time

    Raises:
      UnableToParseFile: if the file cannot be parsed
    """
    while True:
      try:
        dir_buffer = self._file_object.read(16)
        if len(dir_buffer) != 16:
          break
        (time_sec, time_nanosec, _pad) = \
          struct_unpack(self._DB_DIRECTORY, dir_buffer)
        dir_name = self._ParseCString()

        dir_timestamp = time_sec*definitions.NANOSECONDS_PER_SECOND
        dir_timestamp += time_nanosec
        posix_timestamp = posix_time.PosixTimeInNanoseconds(
          timestamp=dir_timestamp)
        yield dir_name.decode(), posix_timestamp

        # skip over file / subdirectory names as they don't have any timestamps
        while True:
          db_type = int.from_bytes(self._file_object.read(1), byteorder="big")

          if db_type == self._DBE_END:
            break
          self._ParseCString()
      except struct_error:
        raise errors.UnableToParseFile('Error in header')

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
    self._file_object.seek(0, os.SEEK_SET)

    header_bytes = self._file_object.read(16)
    if len(header_bytes) != 16:
      raise errors.UnableToParseFile('Unable to read the file header')

    try:
      (magic, conf_size, _version, _check_visibility, _pad) = \
        struct_unpack(self._DB_HEADER, header_bytes)
      if magic != self.DB_MAGIC:
        raise errors.UnableToParseFile('Invalid file magic')

      self.root_path = self._ParseCString()

      # skip configuration section for now
      self._file_object.seek(conf_size, os.SEEK_CUR)
    except struct_error:
      raise errors.UnableToParseFile('Unable to unpack the file header')


class LocateDatabaseParser(interface.FileObjectParser):
  """Parser for locate/updatedb database files"""

  NAME = 'locate_database'
  DATA_FORMAT = 'Locate Database file'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification

    Returns:
      FormatSpecification: format spefication.
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

        event = time_events.DateTimeValuesEvent(folder_timestamp,
          definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)
    except Exception as exception:  # pylint: disable=broad-except
      raise errors.UnableToParseFile(
        'unable to parse locate database with error: {exception}'.format(
          exception=exception))


manager.ParsersManager.RegisterParser(LocateDatabaseParser)
