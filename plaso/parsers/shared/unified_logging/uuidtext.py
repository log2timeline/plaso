# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) uuidtext file parser."""

import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors


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
      os.path.dirname(__file__), 'uuidtext.yaml')

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
        string_offset = data_offset + (offset - range_start_offset)
        format_string = self._ReadStructureFromByteStream(
            self.data[string_offset:], 0, self._cstring_data_map)
        return format_string

    return ''


class UUIDTextFileParser(dtfabric_helper.DtFabricHelper):
  """UUIDText file parser."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'uuidtext.yaml')

  _SUPPORTED_FORMAT_VERSION = (2, 1)

  def __init__(self):
    """Initializes an uuidtext file parser.

    Raises:
      ParseError: if the location of the UUID file is invalid.
    """
    super(UUIDTextFileParser, self).__init__()
    self._uuidtext_file_footer_data_map = self._GetDataTypeMap(
        'uuidtext_file_footer')
    self._uuidtext_file_header_data_map = self._GetDataTypeMap(
        'uuidtext_file_header')

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
