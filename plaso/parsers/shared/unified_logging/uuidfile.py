# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) uuidtext file parser."""

import os

from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import logger


class UUIDTextFile(dtfabric_helper.DtFabricHelper):
  """Apple Unified Logging (AUL) uuidtext file.

  Attributes:
    data (bytes): the format string data.
    entries (list[tuple[int, int, int]]): uuidtext file entries consisting of
        tuples of offset, rolling data size total and data size.
    library_name (str): the library name associated with the UUID file.
    library_path (str): the library path associated with the UUID file.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'uuidfile.yaml')

  def __init__(
      self, data=None, entries=None, library_name=None, library_path=None):
    """Initializes an uuidtext file.

    Args:
      data (Optional[bytes]): the format string data.
      entries (Optional[list[tuple[int, int, int}]]): uuidtext file entries
         consisting of tuples of offset, rolling data size total and data size.
      library_name (Optional[str]): name of the library associated with
          the uuidtext file.
      library_path (Optional[str]): path of the library associated with
          the uuidtext file.
      uuid (uuid.UUID): the UUID.
    """
    super(UUIDTextFile, self).__init__()
    self._cstring_data_map = self._GetDataTypeMap('cstring')
    self.data = data
    self.entries = entries
    self.library_name = library_name
    self.library_path = library_path
    self.uuid = None

  def ReadFormatString(self, offset):
    """Reads the format string located at a specific offset.

    Args:
      offset (int): offset of the format string.

    Returns:
      str: format string at the given offset.

    Raises:
      ParseError: if the format string cannot be read.
    """
    if offset & 0x80000000:
      return '%s'

    for range_start_offset, data_offset, data_len in self.entries:
      range_end_offset = range_start_offset + data_len
      if range_start_offset <= offset < range_end_offset:
        rel_offset = offset - range_start_offset
        return self._ReadStructureFromByteStream(
          self.data[data_offset + rel_offset:],
          0, self._cstring_data_map)

    return ''


class UUIDTextFileParser(dtfabric_helper.DtFabricHelper):
  """UUIDText file parser.

  Attributes:
    file_entry (dfvfs.FileEntry): file entry.
    file_system (dfvfs.FileSystem): file system.
    uuid (uuid.UUID): the UUID.
    uuidtext_location: The path of the uuidtext directory.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'uuidfile.yaml')

  _SUPPORTED_FORMAT_VERSION = (2, 1)

  def __init__(self, file_entry, file_system):
    """Initializes an uuidtext file parser.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
      file_system (dfvfs.FileSystem): file system.

    Raises:
      ParseError: if the location of the UUID file is invalid.
    """
    super(UUIDTextFileParser, self).__init__()
    self._uuidtext_file_footer_data_map = self._GetDataTypeMap(
        'uuidtext_file_footer')
    self._uuidtext_file_header_data_map = self._GetDataTypeMap(
        'uuidtext_file_header')
    self.file_entry = file_entry
    self.file_system = file_system

  # TODO: move this method to the main parser.
  def FindFile(self, parser_mediator, uuid):
    """Finds the UUID File for the given UUID on the file system.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      uuid (str): the requested UUID.

    Returns:
      UUIDTextFile: an uuidtext file or None if not available.
    """
    path_segments = self.file_system.SplitPath(
        self.file_entry.path_spec.location)
    uuidtext_location = self.file_system.JoinPath(
        path_segments[:-3] + ['uuidtext'])

    kwargs = {}
    if self.file_entry.path_spec.parent:
      kwargs['parent'] = self.file_entry.path_spec.parent
    kwargs['location'] = self.file_system.JoinPath(
        [uuidtext_location] + [uuid[0:2]] + [uuid[2:]])
    uuid_file_path_spec = path_spec_factory.Factory.NewPathSpec(
        self.file_entry.path_spec.TYPE_INDICATOR, **kwargs)

    file_object = path_spec_resolver.Resolver.OpenFileObject(
        uuid_file_path_spec)
    if not file_object:
      return None

    try:
      uuidtext_file = self.ParseFileObject(file_object)
      uuidtext_file.uuid = uuid

    except (IOError, errors.ParseError) as exception:
      message = (
          'Unable to parse UUID file: {0:s} with error: '
          '{1!s}').format(uuid, exception)
      logger.warning(message)
      parser_mediator.ProduceExtractionWarning(message)

      uuidtext_file = None

    return uuidtext_file

  def ParseFileObject(self, file_object):
    """Parses an uuidtext file-like object.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Returns:
      UUIDTextFile: an uuidtext file.

    Raises:
      ParseError: if the uuidtext file cannot be parsed.
    """
    file_header, read_size = self._ReadStructureFromFileObject(
        file_object, 0, self._uuidtext_file_header_data_map)

    format_version = (
        file_header.major_format_version, file_header.minor_format_version)
    if format_version != self._SUPPORTED_FORMAT_VERSION:
      raise errors.ParseError(
          'Unsupported format version: {0:d}.{1:d}.'.format(
              file_header.major_format_version,
              file_header.minor_format_version))

    data_size = 0
    entries = []

    for entry in file_header.entry_descriptors:
      entry_tuple = (entry.offset, data_size, entry.data_size)
      entries.append(entry_tuple)

      data_size += entry.data_size

    data = file_object.read(data_size)

    footer_offset = read_size + data_size
    file_footer, _ = self._ReadStructureFromFileObject(
        file_object, footer_offset, self._uuidtext_file_footer_data_map)

    library_name = file_footer.library_path.rsplit('/', maxsplit=1)[-1]
    return UUIDTextFile(
        data=data, entries=entries, library_name=library_name,
        library_path=file_footer.library_path)
