# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) UUIDText file parser."""

import os

from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import interface
from plaso.parsers import logger


class UUIDText(dtfabric_helper.DtFabricHelper):
  """Apple Unified Logging (AUL) UUIDText file.

  Attributes:
    data (str): the raw data.
    entries (tuple[int, int, int]): a tuple of (offset, rolling data size total
       and entry data_size).
    library_name (str): the library name associated with the UUID file.
    library_path (str): the library path associated with the UUID file.
    uuid (uuid.UUID): the UUID.
  """
  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'uuidfile.yaml')

  def __init__(self, library_path, library_name, uuid, data, entries):
    super(UUIDText, self).__init__()
    self.data = data
    self.entries = entries
    self.library_name = library_name
    self.library_path = library_path
    self.uuid = uuid

  def ReadFormatString(self, offset):
    """Reads the format string located at the given offset.

    Args:
      offset (int): Requested offset.

    Returns:
      str: The string at the given offset.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map is missing.
    """
    if offset & 0x80000000:
      return '%s'

    for range_start_offset, data_offset, data_len in self.entries:
      range_end_offset = range_start_offset + data_len
      if range_start_offset <= offset < range_end_offset:
        rel_offset = offset - range_start_offset
        return self._ReadStructureFromByteStream(
          self.data[data_offset + rel_offset:],
          0, self._GetDataTypeMap('cstring'))
    return ''


class UUIDFileParser(
  interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """UUID file parser

  Attributes:
    file_entry (dfvfs.FileEntry): file entry.
    file_system (dfvfs.FileSystem): file system.
    uuid (uuid.UUID): the UUID.
    uuidtext_location: The path of the uuidtext directory.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'uuidfile.yaml')

  def __init__(self, file_entry, file_system):
    """Initializes a UUID file.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
      file_system (dfvfs.FileSystem): file system.
      uuid (UUID): the UUID.
      uuidtext_location (str): File path to the location of DSC files.

    Raises:
      errors.ParseError if the location is invalid.
    """
    super(UUIDFileParser, self).__init__()
    self.file_entry = file_entry
    self.file_system = file_system
    self.uuid = None

    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    self.uuidtext_location = file_system.JoinPath(
        path_segments[:-3] + ['uuidtext'])
    if not os.path.exists(self.uuidtext_location):
      raise errors.ParseError(
        "Invalid UUIDText location: {0:s}".format(self.uuidtext_location))

  def FindFile(self, parser_mediator, uuid):
    """Finds the UUID File for the given UUID on the file system.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      uuid (str): the requested UUID.

    Returns:
      UUIDText object or None if the file was not found.
    """
    self.uuid = uuid
    kwargs = {}
    kwargs['location'] = self.file_system.JoinPath(
        [self.uuidtext_location] + [uuid[0:2]] + [uuid[2:]])
    uuid_file_path_spec = path_spec_factory.Factory.NewPathSpec(
        self.file_entry.path_spec.TYPE_INDICATOR, **kwargs)

    uuid_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        uuid_file_path_spec)

    if not uuid_file_entry:
      return None

    uuid_file_object = uuid_file_entry.GetFileObject()
    try:
      return self.ParseFileObject(parser_mediator, uuid_file_object)
    except (IOError, errors.ParseError) as exception:
      message = (
          'Unable to parse UUID file: {0:s} with error: '
          '{1!s}').format(uuid, exception)
      logger.warning(message)
      parser_mediator.ProduceExtractionWarning(message)
    return None

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a UUID file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    offset = 0
    entries = []

    uuid_header_data_map = self._GetDataTypeMap('uuidtext_file_header')
    uuid_header, size = self._ReadStructureFromFileObject(
        file_object, offset, uuid_header_data_map)
    format_version = (
        uuid_header.major_format_version, uuid_header.minor_format_version)
    if format_version != (2, 1):
      raise errors.ParseError(
          'Unsupported format version: {0:d}.{1:d}.'.format(
              uuid_header.major_format_version,
              uuid_header.minor_format_version))
    data_size = 0
    for entry in uuid_header.entry_descriptors:
      entry_tuple = (entry.offset, data_size, entry.data_size)
      data_size += entry.data_size
      entries.append(entry_tuple)
    data = file_object.read(data_size)
    offset = size + data_size
    uuid_footer, _ = self._ReadStructureFromFileObject(
        file_object, offset, self._GetDataTypeMap('uuidtext_file_footer'))

    return UUIDText(
        library_path=uuid_footer.library_path,
        library_name=os.path.basename(uuid_footer.library_path),
        uuid=self.uuid,
        data=data,
        entries=entries)
