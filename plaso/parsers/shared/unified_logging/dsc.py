# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) shared-cache strings (DSC) file parser."""

import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors


class DSCRange(object):
  """Shared-Cache strings (DSC) range.

  Attributes:
    data_offset (int): the offset of the data.
    path (str): path.
    range_offset (int): the offset of the range.
    range_size (int): the size of the range.
    string (str): The raw string in the DSC file at that range.
    uuid (uuid.UUID): the UUID.
    uuid_index (int): UUID descriptor index.
  """

  def __init__(self):
    """Initializes a shared-cache strings (DSC) range."""
    super(DSCRange, self).__init__()
    self.data_offset = None
    self.path = None
    self.range_offset = None
    self.range_size = None
    self.string = None
    self.uuid = None
    self.uuid_index = None


class DSCUUID(object):
  """Shared-Cache strings (DSC) UUID.

  Attributes:
    path (str): path.
    sender_identifier (uuid.UUID): the sender identifier.
    text_offset (int): the offset of the text.
    text_sizes (int): the size of the text.
  """

  def __init__(self):
    """Initializes a shared-cache strings (DSC) UUID."""
    super(DSCUUID, self).__init__()
    self.path = None
    self.sender_identifier = None
    self.text_offset = None
    self.text_size = None


class DSCFile(object):
  """Shared-Cache strings (DSC) file.

  Attributes:
    ranges (list[DSCRange]): the ranges.
    uuid: The particular UUID of the DSC file.
    uuids (list[DSCUUID]): the UUIDs.
  """

  def __init__(self):
    """Initializes a shared-cache strings (DSC) File."""
    super(DSCFile, self).__init__()
    self.ranges = []
    self.uuid = None
    self.uuids = []

  def ReadFormatString(self, offset):
    """Finds the range in the list of ranges at the given offset."""
    for r in self.ranges:
      if r.range_offset <= offset < (r.range_offset + r.range_size):
        return r
    return None


class DSCFileParser(dtfabric_helper.DtFabricHelper):
  """Shared-Cache strings (DSC) file parser."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'dsc.yaml')

  _SUPPORTED_FORMAT_VERSIONS = ((1, 0), (2, 0))
  _SUPPORTED_MAJOR_VERSIONS = [
      version[0] for version in _SUPPORTED_FORMAT_VERSIONS]

  def _ReadFileHeader(self, file_object):
    """Reads a file header.

    Args:
      file_object (file): file-like object.

    Returns:
      dsc_file_header: a file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('dsc_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    format_version = (
        file_header.major_format_version, file_header.minor_format_version)
    if format_version not in self._SUPPORTED_FORMAT_VERSIONS:
      raise errors.ParseError(
          'Unsupported format version: {0:d}.{1:d}.'.format(
              file_header.major_format_version,
              file_header.minor_format_version))

    return file_header

  def _ReadRangeDescriptors(
      self, file_object, file_offset, major_version, number_of_ranges):
    """Reads the range descriptors.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of range descriptors data relative
          to the start of the file.
      major_version (int): major version of the file.
      number_of_ranges (int): the number of range descriptions to retrieve.

    Yields:
      DSCRange: a range.

    Raises:
      ParseError: if the file cannot be read.
    """
    if major_version not in self._SUPPORTED_MAJOR_VERSIONS:
      raise errors.ParseError('Unsupported format version: {0:d}.'.format(
          major_version))

    if major_version == 1:
      data_type_map_name = 'dsc_range_descriptor_v1'
    else:
      data_type_map_name = 'dsc_range_descriptor_v2'

    data_type_map = self._GetDataTypeMap(data_type_map_name)

    for _ in range(number_of_ranges):
      range_descriptor, record_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += record_size

      dsc_range = DSCRange()
      dsc_range.range_offset = range_descriptor.range_offset
      dsc_range.range_size = range_descriptor.range_size
      dsc_range.data_offset = range_descriptor.data_offset
      dsc_range.uuid_index = range_descriptor.uuid_descriptor_index
      yield dsc_range

  def _ReadUUIDDescriptors(
      self, file_object, file_offset, major_version, number_of_uuids):
    """Reads the UUID descriptors.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of UUID descriptors data relative
          to the start of the file.
      major_version (int): major version of the file
      number_of_uuids (int): the number of UUID descriptions to retrieve.

    Yields:
      DSCUUID: a shared-cache strings (DSC) UUID.

    Raises:
      ParseError: if the file cannot be read.
    """
    if major_version not in self._SUPPORTED_MAJOR_VERSIONS:
      raise errors.ParseError('Unsupported format version: {0:d}.'.format(
          major_version))

    if major_version == 1:
      data_type_map_name = 'dsc_uuid_descriptor_v1'
    else:
      data_type_map_name = 'dsc_uuid_descriptor_v2'

    data_type_map = self._GetDataTypeMap(data_type_map_name)

    for _ in range(number_of_uuids):
      uuid_descriptor, record_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += record_size

      dsc_uuid = DSCUUID()
      dsc_uuid.sender_identifier = uuid_descriptor.sender_identifier
      dsc_uuid.text_offset = uuid_descriptor.text_offset
      dsc_uuid.text_size = uuid_descriptor.text_size

      dsc_uuid.path = self._ReadUUIDPath(
          file_object, uuid_descriptor.path_offset)

      yield dsc_uuid

  def _ReadUUIDPath(self, file_object, file_offset):
    """Reads an UUID path.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the UUID path data relative to the start of
          the file.

    Returns:
      str: UUID path.

    Raises:
      ParseError: if the file cannot be read.
    """
    data_type_map = self._GetDataTypeMap('cstring')

    uuid_path, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return uuid_path

  def ParseFileObject(self, file_object):
    """Parses a shared-cache strings (DSC) file-like object.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Returns:
      DSCFile: a shared-cache strings (DSC) file.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_header = self._ReadFileHeader(file_object)

    file_offset = file_object.tell()

    dsc_file = DSCFile()
    dsc_file.ranges = list(self._ReadRangeDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_ranges))

    file_offset = file_object.tell()

    dsc_file.uuids = list(self._ReadUUIDDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_uuids))

    file_offset = file_object.tell()

    # Fill in strings
    for dsc_range in dsc_file.ranges:
      file_object.seek(dsc_range.data_offset, os.SEEK_SET)
      dsc_range.string = file_object.read(dsc_range.range_size)

    return dsc_file
