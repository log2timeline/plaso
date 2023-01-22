# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) DSC file parser."""

import os

from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib.aul import constants
from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import interface
from plaso.parsers import logger

class DSCRange(object):
  """Shared-Cache Strings (dsc) range.

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
    """Initializes a Shared-Cache Strings (dsc) range."""
    super(DSCRange, self).__init__()
    self.data_offset = None
    self.path = None
    self.range_offset = None
    self.range_size = None
    self.string = None
    self.uuid = None
    self.uuid_index = None


class DSCUUID(object):
  """Shared-Cache Strings (dsc) UUID.

  Attributes:
    path (str): path.
    sender_identifier (uuid.UUID): the sender identifier.
    text_offset (int): the offset of the text.
    text_sizes (int): the size of the text.
  """

  def __init__(self):
    """Initializes a Shared-Cache Strings (dsc) UUID."""
    super(DSCUUID, self).__init__()
    self.path = None
    self.sender_identifier = None
    self.text_offset = None
    self.text_size = None


class DSCFile(object):
  """Shared-Cache Strings (dsc) File.

  Attributes:
    ranges (list[DSCRange]): the ranges.
    uuids (list[DSCUUID]): the UUIDs.
    uuid: The particular UUID of the DSC file.
  """
  def __init__(self):
    """Initializes a Shared-Cache Strings (dsc) File."""
    super(DSCFile, self).__init__()
    self.ranges = []
    self.uuids = []
    self.uuid = None

  def ReadFormatString(self, offset):
    """Finds the range in the list of ranges at the given offset."""
    for r in self.ranges:
      if r.range_offset <= offset < (r.range_offset + r.range_size):
        return r
    return None


class DSCFileParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Shared-Cache Strings (dsc) file parser.

  Attributes:
    ranges (list[DSCRange]): the ranges.
    uuids (list[DSCUUID]): the UUIDs.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'dsc.yaml')

  def __init__(self, file_entry, file_system):
    """Initializes a DSC file.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
      file_system (dfvfs.FileSystem): file system.
      dsc_location (str): File path to the location of DSC files.

    Raises:
      ParseError: if the location of the DSC file is invalid.
    """
    super(DSCFileParser, self).__init__()
    self.file_entry = file_entry
    self.file_system = file_system
    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    self.dsc_location = file_system.JoinPath(
        path_segments[:-3] + ['uuidtext', 'dsc'])
    if not os.path.exists(self.dsc_location):
      raise errors.ParseError(
          "Invalid DSC location: {0:s}".format(self.dsc_location))

  def FindFile(self, parser_mediator, uuid):
    """Finds the DSC file on the file system
       corresponding to the given UUID.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      uuid (str): The desired UUID.

    Returns:
      DSCFile if found, else None.
    """
    kwargs = {}
    kwargs['location'] = self.file_system.JoinPath([self.dsc_location] + [uuid])
    dsc_file_path_spec = path_spec_factory.Factory.NewPathSpec(
        self.file_entry.path_spec.TYPE_INDICATOR, **kwargs)

    dsc_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        dsc_file_path_spec)

    if not dsc_file_entry:
      return None

    dsc_file_object = dsc_file_entry.GetFileObject()
    try:
      ret = self.ParseFileObject(parser_mediator, dsc_file_object)
      ret.uuid = uuid
      return ret
    except (IOError, errors.ParseError) as exception:
      message = (
          'Unable to parse DSC file: {0:s} with error: '
          '{1!s}').format(uuid, exception)
      logger.warning(message)
      parser_mediator.ProduceExtractionWarning(message)
    return None

  def _ReadFileHeader(self, file_object):
    """Reads a dsc file header.

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
    if format_version not in constants.SUPPORTED_DSC_VERSIONS:
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
    if major_version not in [
      version[0] for version in constants.SUPPORTED_DSC_VERSIONS]:
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
      self, file_object, file_offset, version, number_of_uuids):
    """Reads the UUID descriptors.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of UUID descriptors data relative
          to the start of the file.
      version (int): major version of the file
      number_of_uuids (int): the number of UUID descriptions to retrieve.

    Yields:
      DSCUUId: an UUID.

    Raises:
      ParseError: if the file cannot be read.
    """
    if version not in (1, 2):
      raise errors.ParseError('Unsupported format version: {0:d}.'.format(
          version))

    if version == 1:
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

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a shared-cache strings (dsc) file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    ret = DSCFile()
    file_header = self._ReadFileHeader(file_object)

    file_offset = file_object.tell()

    ret.ranges = list(self._ReadRangeDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_ranges))

    file_offset = file_object.tell()

    ret.uuids = list(self._ReadUUIDDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_uuids))

    file_offset = file_object.tell()

    # Fill in strings
    for dsc_range in ret.ranges:
      file_object.seek(dsc_range.data_offset, os.SEEK_SET)
      dsc_range.string = file_object.read(dsc_range.range_size)

    return ret
