# -*- coding: utf-8 -*-
"""Parser for Apple Spotlight store database files."""

from collections import abc as collections

import abc
import os
import zlib

from dfdatetime import cocoa_time as dfdatetime_cocoa_time
from dfdatetime import posix_time as dfdatetime_posix_time

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps

import lz4.block

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class SpotlightStoreIndexValue(object):
  """Index value.

  Attributes:
    table_index (int): table index.
    values_list (list[str]): values list.
  """

  def __init__(self):
    """Initializes an index value."""
    super(SpotlightStoreIndexValue, self).__init__()
    self.table_index = None
    self.values_list = []


class SpotlightStoreMetadataItemEventData(events.EventData):
  """Apple Spotlight store database metadata item event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the item was added
        (kMDItemDateAdded).
    attribute_change_time (dfdatetime.DateTimeValues): date and time
        an attribute was last changed (kMDItemAttributeChangeDate).
    content_creation_time (dfdatetime.DateTimeValues): date and time
        the content was created (kMDItemContentCreationDate).
    content_modification_time (dfdatetime.DateTimeValues): date and time
        the content was last modified (kMDItemContentModificationDate).
    content_type (str): content type of the corresponding file (system) entry
        (kMDItemContentType).
    creation_time (dfdatetime.DateTimeValues): date and time the item was
        created (_kMDItemCreationDate).
    downloaded_time (dfdatetime.DateTimeValues): date and time the item was
        downloaded (kMDItemDownloadedDate).
    file_name (str): name of the corresponding file (system) entry
        (_kMDItemFileName).
    file_system_identifier (int): file system identifier, for example the
        catalog node identifier (CNID) on HFS.
    kind (str): item kind (kMDItemKind).
    modification_time (dfdatetime.DateTimeValues): date and time the item was
        last modified (_kMDItemContentChangeDate).
    parent_file_system_identifier (int): file system identifier of the parent.
    purchase_time  (dfdatetime.DateTimeValues): date and time the item was
        purchased in the AppStore (kMDItemAppStorePurchaseDate).
    snapshot_times (list[dfdatetime.DateTimeValues]): dates and times of
        the creation of backup snaphots (_kTimeMachineOldestSnapshot and
        _kTimeMachineNewestSnapshot).
    update_time (dfdatetime.DateTimeValues): date and time the item was last
        updated.
    used_times (list[dfdatetime.DateTimeValues]): dates and times when the item
        was used (kMDItemUsedDates and kMDItemLastUsedDate).
  """

  DATA_TYPE = 'spotlight:metadata_item'

  def __init__(self):
    """Initializes event data."""
    super(SpotlightStoreMetadataItemEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.added_time = None
    self.attribute_change_time = None
    self.content_creation_time = None
    self.content_modification_time = None
    self.content_type = None
    self.creation_time = None
    self.downloaded_time = None
    self.file_name = None
    self.file_system_identifier = None
    self.kind = None
    self.modification_time = None
    self.parent_file_system_identifier = None
    self.purchase_time  = None
    self.snapshot_times = None
    self.update_time = None
    self.used_times = None


class SpotlightStoreMetadataAttribute(object):
  """Metadata attribute.

  Attributes:
    key (str): key or name of the metadata attribute.
    property_type (int): metadata attribute property type.
    value (object): metadata attribute value.
    value_type (int): metadata attribute value type.
  """

  def __init__(self):
    """Initializes a metadata attribute."""
    super(SpotlightStoreMetadataAttribute, self).__init__()
    self.key = None
    self.property_type = None
    self.value = None
    self.value_type = None


class SpotlightStoreMetadataItem(object):
  """Metadata item.

  Attributes:
    attributes (dict[str, SpotlightStoreMetadataAttribute]): metadata
        attributes.
    data_size (int): size of the record data.
    flags (int): record flags.
    identifier (int): file (system) entry identifier.
    item_identifier (int): item identifier.
    last_update_time (int): last update time.
    parent_identifier (int): parent file (system) entry identifier.
  """

  def __init__(self):
    """Initializes a record."""
    super(SpotlightStoreMetadataItem, self).__init__()
    self.attributes = {}
    self.data_size = 0
    self.flags = 0
    self.identifier = 0
    self.item_identifier = 0
    self.last_update_time = 0
    self.parent_identifier = 0


class BaseSpotlightFile(dtfabric_helper.DtFabricHelper):
  """Shared functionality for Apple Spotlight files."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'spotlight_storedb.yaml')

  def __init__(self):
    """Initializes a Apple Spotlight file."""
    super(BaseSpotlightFile, self).__init__()
    self._file_entry = None
    self._file_object = None

  def Close(self):
    """Closes an Apple Spotlight file.

    Raises:
      IOError: if the file is not opened.
      OSError: if the file is not opened.
    """
    if not self._file_object:
      raise IOError('File not opened')

    self._file_object = None
    self._file_entry = None

  def Open(self, file_entry):
    """Opens an Apple Spotlight file.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Raises:
      IOError: if the file is already opened.
      OSError: if the file is already opened.
    """
    if self._file_object:
      raise IOError('File already opened')

    self._file_entry = file_entry

    file_object = file_entry.GetFileObject()

    self.ReadFileObject(file_object)

    self._file_object = file_object

  @abc.abstractmethod
  def ReadFileObject(self, file_object):
    """Reads an Apple Spotlight file-like object.

    Args:
      file_object (file): file-like object.
    """


class SpotlightStreamsMapDataFile(BaseSpotlightFile):
  """Apple Spotlight database streams map data file (dbStr-#.map.data).

  Attributes:
    stream_values (list[bytes]): stream values.
  """

  def __init__(self, data_size, ranges):
    """Initializes a database streams map data file.

    Args:
      data_size (int): data size.
      ranges (list[tuple[int, int]]): offset and size pairs of the stream value
          data ranges.
    """
    super(SpotlightStreamsMapDataFile, self).__init__()
    self._data_size = data_size
    self._ranges = ranges
    self.stream_values = []

  def _ReadVariableSizeInteger(self, data):
    """Reads a variable size integer.

    Args:
      data (bytes): data.

    Returns:
      tuple[int, int]: integer value and number of bytes read.
    """
    byte_value = data[0]
    bytes_read = 1

    number_of_additional_bytes = 0
    for bitmask in (0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe, 0xff):
      if byte_value & bitmask != bitmask:
        break
      number_of_additional_bytes += 1

    if number_of_additional_bytes > 4:
      byte_value = 0
    elif number_of_additional_bytes > 0:
      byte_value &= bitmask ^ 0xff

    integer_value = int(byte_value)
    while number_of_additional_bytes > 0:
      integer_value <<= 8

      integer_value += int(data[bytes_read])
      bytes_read += 1

      number_of_additional_bytes -= 1

    return integer_value, bytes_read

  def ReadFileObject(self, file_object):
    """Reads a database streams map data file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    data = file_object.read(self._data_size)

    for value_range in self._ranges:
      value_offset, value_size = value_range

      stream_value = data[value_offset:value_offset + value_size]

      self.stream_values.append(stream_value)


class SpotlightStreamsMapHeaderFile(BaseSpotlightFile):
  """Apple Spotlight database streams map header file (dbStr-#.map.header).

  Attributes:
    data_size (int): data size.
    number_of_buckets (int): number of entries in the database streams map
        buckets file (dbStr-#.map.buckets).
    number_of_offsets (int): number of entries in the database streams map
        offsets file (dbStr-#.map.offsets).
  """

  def __init__(self):
    """Initializes a database streams map header file."""
    super(SpotlightStreamsMapHeaderFile, self).__init__()
    self.data_size = None
    self.number_of_buckets = None
    self.number_of_offsets = None

  def ReadFileObject(self, file_object):
    """Reads a database streams map header file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    data_type_map = self._GetDataTypeMap(
        'spotlight_database_streams_map_header')

    streams_map_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    self.data_size = streams_map_header.unknown4
    self.number_of_buckets = streams_map_header.unknown5
    self.number_of_offsets = streams_map_header.unknown6


class SpotlightStreamsMapOffsetsFile(BaseSpotlightFile):
  """Apple Spotlight database streams map offsets file (dbStr-#.map.offsets).

  Attributes:
    ranges (list[tuple[int, int]]): offset and size pairs of the stream value
        data ranges.
  """

  def __init__(self, data_size, number_of_entries):
    """Initializes a database streams map offsets file.

    Args:
      data_size (int): data size.
      number_of_entries (int): number of entries in the offsets file.
    """
    super(SpotlightStreamsMapOffsetsFile, self).__init__()
    self._data_size = data_size
    self._number_of_entries = number_of_entries
    self.ranges = []

  def ReadFileObject(self, file_object):
    """Reads a database streams map offsets file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    data_size = self._number_of_entries * 4
    data = file_object.read(data_size)

    data_type_map = self._GetDataTypeMap('array_of_uint32le')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'number_of_elements': self._number_of_entries})

    try:
      offsets_array = data_type_map.MapByteStream(data, context=context)

    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError(
          f'Unable to parse array of 32-bit offsets with error: {exception!s}')

    index = 0
    last_offset = 0

    for index, offset in enumerate(offsets_array):
      if index == 0:
        last_offset = offsets_array[0]
        continue

      range_size = offset - last_offset

      self.ranges.append((last_offset, range_size))

      last_offset = offset

    if last_offset:
      range_size = self._data_size - last_offset

      self.ranges.append((last_offset, range_size))


class SpotlightStoreDatabaseParser(
    interface.FileEntryParser, dtfabric_helper.DtFabricHelper):
  """Parser for Apple Spotlight store database (store.db) files."""

  NAME = 'spotlight_storedb'
  DATA_FORMAT = 'Apple Spotlight store database (store.db) file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'spotlight_storedb.yaml')

  def __init__(self):
    """Initializes an Apple Spotlight store database parser."""
    super(SpotlightStoreDatabaseParser, self).__init__()
    self._map_values = []
    self._metadata_lists = {}
    self._metadata_localized_strings = {}
    self._metadata_types = {}
    self._metadata_values = {}

  def _DecompressLZ4Block(
      self, file_offset, compressed_data, previous_uncompressed_data):
    """Decompresses LZ4 compressed block.

    Args:
      file_offset (int): file offset.
      compressed_data (bytes): LZ4 compressed data.
      previous_uncompressed_data (bytes): uncompressed data of the previous
          (preceding) block.

    Returns:
      tuple[bytes, int]: uncompressed data and number of bytes read.

    Raises:
      ParseError: if the data cannot be decompressed.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_lz4_block_header')

    try:
      lz4_block_header = data_type_map.MapByteStream(compressed_data)
    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError((
          f'Unable to map LZ4 block header at offset: 0x{file_offset:08x} '
          f'with error: {exception!s}'))

    if lz4_block_header.signature == b'bv41':
      end_of_data_offset = 12 + lz4_block_header.compressed_data_size

      uncompressed_data = lz4.block.decompress(
          compressed_data[12:end_of_data_offset],
          uncompressed_size=lz4_block_header.uncompressed_data_size,
          dict=previous_uncompressed_data)

    elif lz4_block_header.signature == b'bv4-':
      end_of_data_offset = 8 + lz4_block_header.uncompressed_data_size
      uncompressed_data = compressed_data[8:end_of_data_offset]

    else:
      raise errors.ParseError((
          f'Unsupported start of LZ4 block marker at offset: '
          f'0x{file_offset:08x}'))

    return uncompressed_data, end_of_data_offset

  def _DecompressLZ4PageData(self, compressed_page_data, file_offset):
    """Decompresses LZ4 compressed page data.

    Args:
      compressed_page_data (bytes): LZ4 compressed page data.
      file_offset (int): file offset.

    Returns:
      bytes: uncompressed page data.

    Raises:
      ParseError: if the page data cannot be decompressed.
    """
    compressed_data_offset = 0
    compressed_data_size = len(compressed_page_data)

    last_uncompressed_block = None

    uncompressed_blocks = []
    while compressed_data_offset < compressed_data_size:
      lz4_block_marker = compressed_page_data[
          compressed_data_offset:compressed_data_offset + 4]

      if lz4_block_marker == b'bv4$':
        break

      uncompressed_data, bytes_read = self._DecompressLZ4Block(
          file_offset, compressed_page_data[compressed_data_offset:],
          last_uncompressed_block)

      compressed_data_offset += bytes_read
      file_offset += bytes_read

      last_uncompressed_block = uncompressed_data

      uncompressed_blocks.append(uncompressed_data)

    if lz4_block_marker != b'bv4$':
      raise errors.ParseError(
          f'Unsupported end of LZ4 block marker at offset: 0x{file_offset:08x}')

    return b''.join(uncompressed_blocks)

  def _GetDateTimeMetadataItemValue(self, metadata_item, name):
    """Retrieves a date and time value from a metadata item.

    Args:
      metadata_item (SpotlightStoreMetadataItem): a metadata item.
      name (str): name of the attribute.

    Returns:
      dfdatetime.CocoaTime: a date and time value or None if not available.
    """
    value = self._GetMetadataItemValue(metadata_item, name)
    if not value:
      return None

    if isinstance(value, collections.Sequence):
      return dfdatetime_cocoa_time.CocoaTime(timestamp=value[0])

    return dfdatetime_cocoa_time.CocoaTime(timestamp=value)

  def _GetDateTimeMetadataItemValues(self, metadata_item, name):
    """Retrieves a date and time value from a metadata item.

    Args:
      metadata_item (SpotlightStoreMetadataItem): a metadata item.
      name (str): name of the attribute.

    Returns:
      list[dfdatetime.CocoaTime]: date and time values or None if not available.
    """
    value = self._GetMetadataItemValue(metadata_item, name)
    if not value:
      return None

    return [dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
            for timestamp in value]

  def _GetMetadataItemValue(self, metadata_item, name):
    """Retrieves a value from a metadata item.

    Args:
      metadata_item (SpotlightStoreMetadataItem): a metadata item.
      name (str): name of the attribute.

    Returns:
      object: a time value or None if not available.
    """
    metadata_attribute = metadata_item.attributes.get(name, None)
    if not metadata_attribute:
      return None

    return metadata_attribute.value

  def _ParseMetadataItem(self, parser_mediator, metadata_item):
    """Parses an Apple Spotlight store metadata item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      metadata_item (SpotlightStoreMetadataItem): a metadata item.
    """
    event_data = SpotlightStoreMetadataItemEventData()

    # TODO: for identifier 1 extract and process kMDStoreProperties plist

    # Identifier 1 is used for volume metadata.
    if metadata_item.identifier > 1:
      event_data.file_system_identifier = metadata_item.identifier
      event_data.parent_file_system_identifier = metadata_item.parent_identifier

    snapshot_times = []

    date_time = self._GetDateTimeMetadataItemValue(
        metadata_item, '_kTimeMachineOldestSnapshot')
    if date_time:
      snapshot_times.append(date_time)

    date_time = self._GetDateTimeMetadataItemValue(
        metadata_item, '_kTimeMachineNewestSnapshot')
    if date_time:
      snapshot_times.append(date_time)

    used_times = self._GetDateTimeMetadataItemValues(
        metadata_item, 'kMDItemUsedDates') or []

    date_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemLastUsedDate')
    if date_time:
      used_times.append(date_time)

    # TODO: add more attribute values.
    event_data.added_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemDateAdded')
    event_data.attribute_change_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemAttributeChangeDate')
    event_data.content_creation_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemContentCreationDate')
    event_data.content_modification_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemContentModificationDate')
    event_data.content_type = self._GetMetadataItemValue(
        metadata_item, 'kMDItemContentType')
    event_data.creation_time = self._GetDateTimeMetadataItemValue(
        metadata_item, '_kMDItemCreationDate')
    event_data.downloaded_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemDownloadedDate')
    event_data.file_name = self._GetMetadataItemValue(
        metadata_item, '_kMDItemFileName')
    event_data.kind = self._GetMetadataItemValue(
        metadata_item, 'kMDItemKind')
    event_data.modification_time = self._GetDateTimeMetadataItemValue(
        metadata_item, '_kMDItemContentChangeDate')
    event_data.purchase_time = self._GetDateTimeMetadataItemValue(
        metadata_item, 'kMDItemAppStorePurchaseDate')
    event_data.snapshot_times = snapshot_times or None
    event_data.used_times = used_times or None

    if metadata_item.last_update_time:
      event_data.update_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=metadata_item.last_update_time)

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecord(self, parser_mediator, page_data, page_data_offset):
    """Parses a record for its metadata item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      page_data (bytes): page data.
      page_data_offset (int): offset of the page value relative to the start
          of the page data.

    Returns:
      int: number of bytes read.

    Raises:
      ParseError: if the record cannot be read.
    """
    metadata_item, bytes_read = self._ReadRecordHeader(
        page_data[page_data_offset:], page_data_offset)

    page_data_offset += bytes_read
    record_data_offset = bytes_read

    metadata_type_index = 0

    try:
      while record_data_offset < metadata_item.data_size:
        relative_metadata_type_index, bytes_read = (
            self._ReadVariableSizeInteger(page_data[page_data_offset:]))

        page_data_offset += bytes_read
        record_data_offset += bytes_read

        metadata_type_index += relative_metadata_type_index

        metadata_type = self._metadata_types.get(metadata_type_index, None)
        metadata_attribute, bytes_read = self._ReadMetadataAttribute(
            metadata_type, page_data[page_data_offset:])

        page_data_offset += bytes_read
        record_data_offset += bytes_read

        metadata_item.attributes[metadata_attribute.key] = metadata_attribute

      self._ParseMetadataItem(parser_mediator, metadata_item)

    except errors.ParseError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to read metadata item: 0x{0:2x} with error: {1!s}'.format(
              metadata_item.identifier, exception))

    return 4 + metadata_item.data_size

  def _ParseRecordPageValues(self, parser_mediator, page_data):
    """Parses the record page values.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      page_data (bytes): page data.

    Raises:
      ParseError: if the property page values cannot be read.
    """
    page_data_offset = 0
    page_data_size = len(page_data)

    while page_data_offset < page_data_size:
      bytes_read = self._ParseRecord(
          parser_mediator, page_data, page_data_offset)

      page_data_offset += bytes_read

  def _ReadFileHeader(self, file_object):
    """Reads the file header.

    Args:
      file_object (file): file-like object.

    Returns:
      spotlight_store_db_file_header: file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    return file_header

  def _ReadIndexPageValues(self, page_header, page_data, property_table):
    """Reads the index page values.

    Args:
      page_header (spotlight_store_db_property_page_header): page header.
      page_data (bytes): page data.
      property_table (dict[int, SpotlightStoreIndexValue]): property table in
          which to store the property page values.

    Raises:
      ParseError: if the property page values cannot be read.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_property_value81')
    index_values_data_type_map = self._GetDataTypeMap(
        'spotlight_store_db_index_values')

    page_data_offset = 12
    page_data_size = page_header.used_page_size - 20
    page_value_index = 0

    while page_data_offset < page_data_size:
      try:
        property_value = data_type_map.MapByteStream(
            page_data[page_data_offset:])
      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            'Unable to map property value data at offset: 0x{0:08x} with '
            'error: {1!s}').format(page_data_offset, exception))

      page_value_size = 4

      index_size, bytes_read = self._ReadVariableSizeInteger(
          page_data[page_data_offset + page_value_size:])

      _, padding_size = divmod(index_size, 4)

      page_value_size += bytes_read + padding_size
      index_size -= padding_size

      context = dtfabric_data_maps.DataTypeMapContext(values={
          'index_size': index_size})

      try:
        index_values = index_values_data_type_map.MapByteStream(
            page_data[page_data_offset + page_value_size:], context=context)

      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            'Unable to parse index data at offset: 0x{0:08x} with error: '
            '{1:s}').format(page_data_offset + page_value_size, exception))

      page_value_size += index_size

      values_list = []
      for metadata_value_index in index_values:
        metadata_value = self._metadata_values.get(metadata_value_index, None)
        value_string = getattr(metadata_value, 'value_name', '')
        values_list.append(value_string)

      index_value = SpotlightStoreIndexValue()
      index_value.table_index = property_value.table_index
      index_value.values_list = values_list

      property_table[index_value.table_index] = index_value

      page_data_offset += page_value_size
      page_value_index += 1

  def _ReadIndexStreamsMap(
      self, parent_file_entry, streams_map_number, property_table):
    """Reads an index streams map.

    Args:
      parent_file_entry (dfvfs.FileEntry): parent of the Spotlight store.db
          file entry.
      streams_map_number (int): number of the streams map.
      property_table (dict[int, SpotlightStoreIndexValue]): property table in
          which to store the index values.

    Raises:
      ParseError: if the index streams map cannot be read.
    """
    stream_values = self._ReadStreamsMap(parent_file_entry, streams_map_number)

    index_values_data_type_map = self._GetDataTypeMap(
        'spotlight_store_db_index_values')

    for index, stream_value in enumerate(stream_values):
      if index == 0:
        continue

      _, data_offset = self._ReadVariableSizeInteger(stream_value)

      index_size, bytes_read = self._ReadVariableSizeInteger(
          stream_value[data_offset:])

      data_offset += bytes_read

      _, padding_size = divmod(index_size, 4)

      index_size -= padding_size

      context = dtfabric_data_maps.DataTypeMapContext(values={
          'index_size': index_size})

      try:
        index_values = index_values_data_type_map.MapByteStream(
            stream_value[data_offset + padding_size:], context=context)

      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            f'Unable to map stream value: {index:d} data with error: '
            f'{exception!s}'))

      values_list = []
      for metadata_value_index in index_values:
        metadata_value = self._metadata_values.get(metadata_value_index, None)
        value_string = getattr(metadata_value, 'value_name', '')
        values_list.append(value_string)

      index_value = SpotlightStoreIndexValue()
      index_value.table_index = index
      index_value.values_list = values_list

      property_table[index] = index_value

  def _ReadMapPage(self, file_object, file_offset):
    """Reads a map page.

    Args:
      file_object (file): file-like object.
      file_offset (int): file offset.

    Returns:
      spotlight_store_db_map_page_header: page header.

    Raises:
      ParseError: if the map page cannot be read.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_map_page_header')

    page_header, page_header_size = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    file_offset += page_header_size

    self._ReadMapPageValues(page_header, file_object, file_offset)

    return page_header

  def _ReadMapPages(self, file_object, map_offset, map_size):
    """Reads the map pages.

    Args:
      file_object (file): file-like object.
      map_offset (int): map offset.
      map_size (int): map size.

    Raises:
      ParseError: if the map pages cannot be read.
    """
    map_end_offset = map_offset + map_size

    while map_offset < map_end_offset:
      page_header = self._ReadMapPage(file_object, map_offset)

      map_offset += page_header.page_size

  def _ReadMapPageValues(self, page_header, file_object, file_offset):
    """Reads the map page values.

    Args:
      page_header (spotlight_store_db_map_page_header): page header.
      file_object (file): file-like object.
      file_offset (int): file offset.

    Raises:
      ParseError: if the map page values cannot be read.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_map_page_value')

    for _ in range(page_header.number_of_map_values):
      map_value, map_value_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      self._map_values.append(map_value)

      file_offset += map_value_size

  def _ReadMetadataAttribute(self, metadata_type, data):
    """Reads a metadata attribute.

    Args:
      metadata_type (spotlight_store_db_property_value11): metadata type
          property value.
      data (bytes): data.

    Returns:
      tuple[SpotlightStoreMetadataAttribute, int]: metadata attribute and
          number of bytes read.
    """
    value_type = getattr(metadata_type, 'value_type', None)
    if value_type is None:
      return None, 0

    key_name = getattr(metadata_type, 'key_name', None)
    property_type = getattr(metadata_type, 'property_type', None)

    if key_name == 'kMDStoreAccumulatedSizes':
      bytes_read = len(data)
      value = data

    elif value_type in (0x00, 0x02, 0x06):
      value, bytes_read = self._ReadVariableSizeInteger(data)

    elif value_type == 0x07:
      value, bytes_read = self._ReadMetadataAttributeVariableSizeIntegerValue(
          property_type, data)

    elif value_type == 0x08:
      value, bytes_read = self._ReadMetadataAttributeByteValue(
          property_type, data)

    elif value_type == 0x09:
      value, bytes_read = self._ReadMetadataAttributeFloat32Value(
          property_type, data)

    elif value_type in (0x0a, 0x0c):
      value, bytes_read = self._ReadMetadataAttributeFloat64Value(
          property_type, data)

    elif value_type == 0x0b:
      value, bytes_read = self._ReadMetadataAttributeStringValue(
          property_type, data)

    elif value_type == 0x0e:
      data_size, bytes_read = self._ReadVariableSizeInteger(data)

      value = data[bytes_read:bytes_read + data_size]
      bytes_read += data_size

      # TODO: decode binary data e.g. UUID

    elif value_type == 0x0f:
      value, bytes_read = self._ReadMetadataAttributeReferenceValue(
          property_type, data)

    else:
      # TODO: value type 0x01, 0x03, 0x04, 0x05, 0x0d
      value, bytes_read = None, 0

    metadata_attribute = SpotlightStoreMetadataAttribute()
    metadata_attribute.key = getattr(metadata_type, 'key_name', None)
    metadata_attribute.property_type = property_type
    metadata_attribute.value = value
    metadata_attribute.value_type = value_type

    return metadata_attribute, bytes_read

  def _ReadMetadataAttributeByteValue(self, property_type, data):
    """Reads a metadata attribute byte value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.

    Raises:
      ParseError: if the metadata attribute byte value cannot be read.
    """
    if property_type & 0x02:
      data_size, bytes_read = self._ReadVariableSizeInteger(data)
    else:
      data_size, bytes_read = 1, 0

    data_type_map = self._GetDataTypeMap('array_of_byte')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'elements_data_size': data_size})

    try:
      array_of_values = data_type_map.MapByteStream(
          data[bytes_read:bytes_read + data_size], context=context)

    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError(
          'Unable to parse array of byte values with error: {0!s}'.format(
              exception))

    if bytes_read == 0:
      value = array_of_values[0]
    else:
      value = array_of_values

    bytes_read += data_size

    return value, bytes_read

  def _ReadMetadataAttributeFloat32Value(self, property_type, data):
    """Reads a metadata attribute 32-bit floating-point value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.

    Raises:
      ParseError: if the metadata attribute 32-bit floating-point value cannot
          be read.
    """
    if property_type & 0x02 == 0x00:
      data_size, bytes_read = 4, 0
    else:
      data_size, bytes_read = self._ReadVariableSizeInteger(data)

    data_type_map = self._GetDataTypeMap('array_of_float32')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'elements_data_size': data_size})

    try:
      array_of_values = data_type_map.MapByteStream(
          data[bytes_read:bytes_read + data_size], context=context)

    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError((
          'Unable to parse array of 32-bit floating-point values with error: '
          '{0!s}').format(exception))

    if bytes_read == 0:
      value = array_of_values[0]
    else:
      value = array_of_values

    bytes_read += data_size

    return value, bytes_read

  def _ReadMetadataAttributeFloat64Value(self, property_type, data):
    """Reads a metadata attribute 64-bit floating-point value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.

    Raises:
      ParseError: if the metadata attribute 64-bit floating-point value cannot
          be read.
    """
    if property_type & 0x02 == 0x00:
      data_size, bytes_read = 8, 0
    else:
      data_size, bytes_read = self._ReadVariableSizeInteger(data)

    data_type_map = self._GetDataTypeMap('array_of_float64')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'elements_data_size': data_size})

    try:
      array_of_values = data_type_map.MapByteStream(
          data[bytes_read:bytes_read + data_size], context=context)

    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError((
          'Unable to parse array of 64-bit floating-point values with error: '
          '{0!s}').format(exception))

    if bytes_read == 0:
      value = array_of_values[0]
    else:
      value = array_of_values

    bytes_read += data_size

    return value, bytes_read

  def _ReadMetadataAttributePageValues(
      self, page_header, page_data, property_table):
    """Reads the metadata atribute page values.

    Args:
      page_header (spotlight_store_db_property_page_header): page header.
      page_data (bytes): page data.
      property_table (dict[int, object]): property table in which to store the
          property page values.

    Raises:
      ParseError: if the property page values cannot be read.
    """
    if page_header.property_table_type == 0x00000011:
      data_type_map = self._GetDataTypeMap(
          'spotlight_store_db_property_value11')

    elif page_header.property_table_type == 0x00000021:
      data_type_map = self._GetDataTypeMap(
          'spotlight_store_db_property_value21')

    page_data_offset = 12
    page_data_size = page_header.used_page_size - 20
    page_value_index = 0

    while page_data_offset < page_data_size:
      context = dtfabric_data_maps.DataTypeMapContext()

      try:
        property_value = data_type_map.MapByteStream(
            page_data[page_data_offset:], context=context)
      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            'Unable to map property value data at offset: 0x{0:08x} with '
            'error: {1!s}').format(page_data_offset, exception))

      property_table[property_value.table_index] = property_value

      page_data_offset += context.byte_size
      page_value_index += 1

  def _ReadMetadataAttributeReferenceValue(self, property_type, data):
    """Reads a metadata attribute reference value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.

    Raises:
      ParseError: if the metadata attribute reference value cannot be read.
    """
    table_index, bytes_read = self._ReadVariableSizeInteger(data)

    if property_type & 0x03 == 0x03:
      metadata_localized_strings = self._metadata_localized_strings.get(
          table_index, None)
      value_list = getattr(metadata_localized_strings, 'values_list', [])

      value = '(null)'
      if value_list:
        value = value_list[0]
        if '\x16\x02' in value:
          value = value.split('\x16\x02')[0]

    elif property_type & 0x03 == 0x02:
      metadata_list = self._metadata_lists.get(table_index, None)
      value = getattr(metadata_list, 'values_list', [])

    else:
      metadata_value = self._metadata_values.get(table_index, None)
      value = getattr(metadata_value, 'value_name', '(null)')

    return value, bytes_read

  def _ReadMetadataAttributeStringValue(self, property_type, data):
    """Reads a metadata attribute string value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.

    Raises:
      ParseError: if the metadata attribute string value cannot be read.
    """
    data_size, bytes_read = self._ReadVariableSizeInteger(data)

    data_type_map = self._GetDataTypeMap('array_of_cstring')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'elements_data_size': data_size})

    try:
      array_of_values = data_type_map.MapByteStream(
          data[bytes_read:bytes_read + data_size], context=context)

    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError(
          'Unable to parse array of string values with error: {0!s}'.format(
              exception))

    if property_type & 0x03 == 0x03:
      value = array_of_values[0]
      if '\x16\x02' in value:
        value = value.split('\x16\x02')[0]
    elif property_type & 0x03 == 0x02:
      value = array_of_values
    else:
      value = array_of_values[0]

    bytes_read += data_size

    return value, bytes_read

  def _ReadMetadataAttributeVariableSizeIntegerValue(self, property_type, data):
    """Reads a metadata attribute variable size integer value.

    Args:
      property_type (int): metadata attribute property type.
      data (bytes): data.

    Returns:
      tuple[object, int]: value and number of bytes read.
    """
    if property_type & 0x02 == 0x00:
      return self._ReadVariableSizeInteger(data)

    data_size, bytes_read = self._ReadVariableSizeInteger(data)

    array_of_values = []

    data_offset = 0
    while data_offset < data_size:
      integer_value, integer_value_size = self._ReadVariableSizeInteger(
          data[data_offset:data_size])

      data_offset += integer_value_size

      array_of_values.append(integer_value)

    bytes_read += data_size

    return array_of_values, bytes_read

  def _ReadMetadataAttributeStreamsMap(
      self, parent_file_entry, streams_map_number, property_table):
    """Reads a metadata attribute streams map.

    Args:
      parent_file_entry (dfvfs.FileEntry): parent of the Spotlight store.db
          file entry.
      streams_map_number (int): number of the streams map.
      property_table (dict[int, object]): property table in which to store the
          metadata attribute values.

    Raises:
      ParseError: if the metadata attribute streams map cannot be read.
    """
    stream_values = self._ReadStreamsMap(parent_file_entry, streams_map_number)

    if streams_map_number == 1:
      data_type_map = self._GetDataTypeMap(
          'spotlight_metadata_attribute_type')

    elif streams_map_number == 2:
      data_type_map = self._GetDataTypeMap(
          'spotlight_metadata_attribute_value')

    for index, stream_value in enumerate(stream_values):
      if index == 0:
        continue

      data_size, data_offset = self._ReadVariableSizeInteger(stream_value)

      if data_offset + data_size != len(stream_value):
        # Stream values where the data size does not match appear to contain
        # remnant data.
        continue

      try:
        property_value = data_type_map.MapByteStream(stream_value[data_offset:])
      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            f'Unable to map stream value: {index:d} data with error: '
            f'{exception!s}'))

      property_value.table_index = index

      property_table[index] = property_value

  def _ReadPropertyPage(self, file_object, file_offset, property_table):
    """Reads a property page.

    Args:
      file_object (file): file-like object.
      file_offset (int): file offset.
      property_table (dict[int, object]): property table in which to store the
          property page values.

    Returns:
      tuple[spotlight_store_db_property_page_header, int]: page header and next
          property page block number.

    Raises:
      ParseError: if the property page cannot be read.
    """
    page_header, bytes_read = self._ReadPropertyPageHeader(
        file_object, file_offset)

    if page_header.property_table_type not in (
        0x00000011, 0x00000021, 0x00000041, 0x00000081):
      raise errors.ParseError(
          'Unsupported property table type: 0x{0:08x}'.format(
              page_header.property_table_type))

    page_data = file_object.read(page_header.page_size - bytes_read)

    data_type_map = self._GetDataTypeMap(
        'spotlight_store_db_property_values_header')

    file_offset += bytes_read

    page_values_header = self._ReadStructureFromByteStream(
        page_data, file_offset, data_type_map)

    if page_header.property_table_type in (0x00000011, 0x00000021):
      self._ReadMetadataAttributePageValues(
          page_header, page_data, property_table)

    elif page_header.property_table_type == 0x00000081:
      self._ReadIndexPageValues(page_header, page_data, property_table)

    return page_header, page_values_header.next_block_number

  def _ReadPropertyPageHeader(self, file_object, file_offset):
    """Reads a property page header.

    Args:
      file_object (file): file-like object.
      file_offset (int): file offset.

    Returns:
      tuple[spotlight_store_db_property_page_header, int]: page header and next
          property page block number.

    Raises:
      ParseError: if the property page header cannot be read.
    """
    data_type_map = self._GetDataTypeMap(
        'spotlight_store_db_property_page_header')

    return self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

  def _ReadPropertyPages(self, file_object, block_number, property_table):
    """Reads the property pages.

    Args:
      file_object (file): file-like object.
      block_number (int): block number.
      property_table (dict[int, object]): property table in which to store the
          property page values.

    Raises:
      ParseError: if the property pages cannot be read.
    """
    file_offset = block_number * 0x1000
    while file_offset != 0:
      _, next_block_number = self._ReadPropertyPage(
          file_object, file_offset, property_table)

      file_offset = next_block_number * 0x1000

  def _ReadRecordHeader(self, data, page_data_offset):
    """Reads a record header.

    Args:
      data (bytes): data.
      page_data_offset (int): offset of the page value relative to the start
          of the page data.

    Returns:
      tuple[SpotlightStoreMetadataItem, int]: metadata item and number of
          bytes read.

    Raises:
      ParseError: if the record page cannot be read.
    """
    data_type_map = self._GetDataTypeMap('spotlight_store_db_record')

    context = dtfabric_data_maps.DataTypeMapContext()

    try:
      record = data_type_map.MapByteStream(data, context=context)
    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError((
          'Unable to map record at offset: 0x{0:08x} with error: '
          '{1!s}').format(page_data_offset, exception))

    data_offset = context.byte_size

    identifier, bytes_read = self._ReadVariableSizeInteger(data[data_offset:])

    data_offset += bytes_read

    flags = data[data_offset]

    data_offset += 1

    value_names = ['item_identifier', 'parent_identifier', 'last_update_time']
    values, bytes_read = self._ReadVariableSizeIntegers(
        data[data_offset:], value_names)

    data_offset += bytes_read

    metadata_item = SpotlightStoreMetadataItem()
    metadata_item.data_size = record.data_size
    metadata_item.flags = flags
    metadata_item.identifier = identifier
    metadata_item.item_identifier = values.get('item_identifier')
    metadata_item.last_update_time = values.get('last_update_time')
    metadata_item.parent_identifier = values.get('parent_identifier')

    return metadata_item, data_offset

  def _ReadRecordPage(self, file_object, file_offset):
    """Reads a record page.

    Args:
      file_object (file): file-like object.
      file_offset (int): file offset.

    Returns:
      tuple[spotlight_store_db_property_page_header, bytes]: page header and
          page data.

    Raises:
      ParseError: if the property page cannot be read.
    """
    page_header, bytes_read = self._ReadPropertyPageHeader(
        file_object, file_offset)

    if page_header.property_table_type not in (
        0x00000009, 0x00001009, 0x00005009):
      raise errors.ParseError(
          'Unsupported property table type: 0x{0:08x}'.format(
              page_header.property_table_type))

    page_data = file_object.read(page_header.page_size - bytes_read)

    file_offset += bytes_read

    if page_header.uncompressed_page_size > 0:
      compressed_page_data = page_data

      if (page_header.property_table_type & 0x00001000 and
          compressed_page_data[0:4] in (b'bv41', b'bv4-')):
        page_data = self._DecompressLZ4PageData(
            compressed_page_data, file_offset)

      elif compressed_page_data[0] == 0x78:
        page_data = zlib.decompress(compressed_page_data)

      else:
        raise errors.ParseError('Unsupported compression type')

    return page_header, page_data

  def _ReadStreamsMap(self, parent_file_entry, streams_map_number):
    """Reads a streams map.

    Args:
      parent_file_entry (dfvfs.FileEntry): parent of the Spotlight store.db
          file entry.
      streams_map_number (int): number of the streams map.

    Returns:
      list[bytes]: stream values.

    Raises:
      ParseError: if the streams map cannot be read.
    """
    header_file_entry = parent_file_entry.GetSubFileEntryByName(
        f'dbStr-{streams_map_number:d}.map.header')

    streams_map_header = SpotlightStreamsMapHeaderFile()
    streams_map_header.Open(header_file_entry)

    data_size = streams_map_header.data_size
    number_of_offsets = streams_map_header.number_of_offsets

    streams_map_header.Close()

    offsets_file_entry = parent_file_entry.GetSubFileEntryByName(
        f'dbStr-{streams_map_number:d}.map.offsets')

    streams_map_offsets = SpotlightStreamsMapOffsetsFile(
        data_size, number_of_offsets)
    streams_map_offsets.Open(offsets_file_entry)

    ranges = streams_map_offsets.ranges

    streams_map_offsets.Close()

    data_file_entry = parent_file_entry.GetSubFileEntryByName(
        f'dbStr-{streams_map_number:d}.map.data')

    streams_map_data = SpotlightStreamsMapDataFile(data_size, ranges)
    streams_map_data.Open(data_file_entry)

    stream_values = streams_map_data.stream_values

    streams_map_data.Close()

    return stream_values

  def _ReadVariableSizeInteger(self, data):
    """Reads a variable size integer.

    Args:
      data (bytes): data.

    Returns:
      tuple[int, int]: integer value and number of bytes read.
    """
    byte_value = data[0]
    bytes_read = 1

    number_of_additional_bytes = 0
    for bitmask in (0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe, 0xff):
      if byte_value & bitmask != bitmask:
        break
      number_of_additional_bytes += 1

    if number_of_additional_bytes > 4:
      byte_value = 0
    elif number_of_additional_bytes > 0:
      byte_value &= bitmask ^ 0xff

    integer_value = int(byte_value)
    while number_of_additional_bytes > 0:
      integer_value <<= 8

      integer_value += int(data[bytes_read])
      bytes_read += 1

      number_of_additional_bytes -= 1

    return integer_value, bytes_read

  def _ReadVariableSizeIntegers(self, data, names):
    """Reads variable size integers.

    Args:
      data (bytes): data.
      names (list[str]): names to identify the integer values.

    Returns:
      tuple[dict[str, int], int]: integer values per name and number of bytes
          read.
    """
    values = {}

    data_offset = 0
    for name in names:
      integer_value, bytes_read = self._ReadVariableSizeInteger(
          data[data_offset:])

      data_offset += bytes_read

      values[name] = integer_value

    return values, data_offset

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'8tsd', offset=0)
    return format_specification

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an Apple Spotlight store database file entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): a file entry to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    parent_file_entry = file_entry.GetParentFileEntry()

    file_object = file_entry.GetFileObject()

    try:
      file_header = self._ReadFileHeader(file_object)
    except (ValueError, errors.ParseError):
      raise errors.WrongParser('Unable to parse file header.')

    try:
      self._map_values = []
      self._ReadMapPages(
          file_object, file_header.map_offset, file_header.map_size)

      self._metadata_types = {}
      if not file_header.metadata_types_block_number:
        self._ReadMetadataAttributeStreamsMap(
            parent_file_entry, 1, self._metadata_types)
      else:
        self._ReadPropertyPages(
            file_object, file_header.metadata_types_block_number,
            self._metadata_types)

      self._metadata_values = {}
      if not file_header.metadata_values_block_number:
        self._ReadMetadataAttributeStreamsMap(
            parent_file_entry, 2, self._metadata_values)
      else:
        self._ReadPropertyPages(
            file_object, file_header.metadata_values_block_number,
            self._metadata_values)

      # Note that the content of this property page is currently unknown.
      if not file_header.unknown_values41_block_number:
        self._ReadIndexStreamsMap(parent_file_entry, 3, {})
      else:
        self._ReadPropertyPages(
            file_object, file_header.unknown_values41_block_number, {})

      self._metadata_lists = {}
      if not file_header.metadata_lists_block_number:
        self._ReadIndexStreamsMap(parent_file_entry, 4, self._metadata_lists)
      else:
        self._ReadPropertyPages(
            file_object, file_header.metadata_lists_block_number,
            self._metadata_lists)

      self._metadata_localized_strings = {}
      if not file_header.metadata_localized_strings_block_number:
        self._ReadIndexStreamsMap(
            parent_file_entry, 5, self._metadata_localized_strings)
      else:
        self._ReadPropertyPages(
            file_object, file_header.metadata_localized_strings_block_number,
            self._metadata_localized_strings)

    except errors.ParseError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to read store database with error: {0!s}'.format(
              exception))
      return

    for map_value in self._map_values:
      file_offset = map_value.block_number * 0x1000

      try:
        _, page_data = self._ReadRecordPage(file_object, file_offset)

        self._ParseRecordPageValues(parser_mediator, page_data)

      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read record page at offset: 0x{0:08x} with error: '
            '{1!s}').format(file_offset, exception))
        continue


manager.ParsersManager.RegisterParser(SpotlightStoreDatabaseParser)
