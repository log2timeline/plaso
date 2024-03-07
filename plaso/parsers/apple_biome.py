"""A parser for Apple biome files, aka SEGB files."""
import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class AppleBiomeFile(dtfabric_helper.DtFabricHelper):
  """Apple biome (aka SEGB) file.

  Attributes:
    header (segb_header): Header of the file.
    records (list[segb_record]): All the records recovered from the file.
    version (str): file version number.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'apple_biome.yaml')

  def __init__(self):
    """Initializes an Apple biome file."""
    super(AppleBiomeFile, self).__init__()
    self.header = None
    self.records = []
    self.version = None

  def _ReadAllRecords(self, file_object, starting_offset):
    """Iterates over all the records in the Apple biome file.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      starting_offset (int): offset from which to start reading records.
    """
    data_type_map = self._GetDataTypeMap(self.version)
    file_size = file_object.get_size()
    file_offset = starting_offset

    while file_offset < file_size:
      record, record_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += record_size

      # Padding
      _, alignment = divmod(file_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      file_offset += alignment

      # Case where the record has a blank header and no content
      # record_size includes the record header, record.size only counts content
      # This signals the end of records.
      if record_size == 32 and record.size == 0:
        break

      # Case where the record has a valid header but the content is all nulls.
      # These can be at the top of the file.
      if set(record.protobuf) == {0}:
        continue

      self.records.append(record)

  def _ReadFileHeader(self, file_object):
    """Determines the version of the Apple biome file and returns its header.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      File header and data size of the header.
    """
    data_type_map = self._GetDataTypeMap('segb_header_v1')

    header, header_size = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    if header.segb_magic == b'SEGB':
      return header, header_size

    return None, 0

  def Open(self, file_object):
    """Opens an Apple biome file.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      ValueError: if the file object is missing.
      errors.WrongParser: if the segb_record version is not recognized.
    """
    if not file_object:
      raise ValueError('Missing file_object.')

    self.header, header_size = self._ReadFileHeader(file_object)

    if header_size == 56:
      self.version = 'segb_record_v1'
    else:
      raise errors.WrongParser('File could not be parsed.')

    self._ReadAllRecords(file_object, header_size)


class AppleBiomeParser(interface.FileObjectParser):
  """Parses Apple biome file-like objects."""

  NAME = 'biome'
  DATA_FORMAT = 'Apple biome'

  _plugin_classes = {}

  def __int__(self):
    """Initializes a parser."""
    super(AppleBiomeParser, self).__init__()

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'SEGB', offset=52)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Apple biome files.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    biome_file = AppleBiomeFile()
    biome_file.Open(file_object)

    for plugin_name, plugin in self._plugins_per_name.items():
      if parser_mediator.abort:
        break

      profiling_name = '/'.join([self.NAME, plugin.NAME])
      parser_mediator.SampleFormatCheckStartTiming(profiling_name)

      try:
        result = False
        # Some of the records may have missing fields
        for record in biome_file.records:
          result = plugin.CheckRequiredSchema(record.protobuf)
          if result:
            break
      finally:
        parser_mediator.SampleFormatCheckStopTiming(profiling_name)

      if not result:
        continue

      parser_mediator.SampleStartTiming(profiling_name)

      try:
        plugin.UpdateChainAndProcess(parser_mediator, biome_file=biome_file)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse Apple biome file with error: '
            '{1!s}').format(plugin_name, exception))

      finally:
        parser_mediator.SampleStopTiming(profiling_name)


manager.ParsersManager.RegisterParser(AppleBiomeParser)
