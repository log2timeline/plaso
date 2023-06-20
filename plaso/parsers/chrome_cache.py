# -*- coding: utf-8 -*-
"""Parser for Google Chrome and Chromium Cache files."""

import os

from dfdatetime import webkit_time as dfdatetime_webkit_time
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class CacheAddress(object):
  """Chrome cache address.

  Attributes:
    block_number (int): block data file number.
    block_offset (int): offset within the block data file.
    block_size (int): block size.
    filename (str): name of the block data file.
    value (int): cache address.
  """
  FILE_TYPE_SEPARATE = 0
  FILE_TYPE_BLOCK_RANKINGS = 1
  FILE_TYPE_BLOCK_256 = 2
  FILE_TYPE_BLOCK_1024 = 3
  FILE_TYPE_BLOCK_4096 = 4

  _BLOCK_DATA_FILE_TYPES = [
      FILE_TYPE_BLOCK_RANKINGS,
      FILE_TYPE_BLOCK_256,
      FILE_TYPE_BLOCK_1024,
      FILE_TYPE_BLOCK_4096]

  _FILE_TYPE_BLOCK_SIZES = [0, 36, 256, 1024, 4096]

  def __init__(self, cache_address):
    """Initializes a cache address.

    Args:
      cache_address (int): cache address.
    """
    super(CacheAddress, self).__init__()
    self.block_number = None
    self.block_offset = None
    self.block_size = None
    self.filename = None
    self.value = cache_address

    if cache_address & 0x80000000:
      self.is_initialized = 'True'
    else:
      self.is_initialized = 'False'

    self.file_type = (cache_address & 0x70000000) >> 28
    if not cache_address == 0x00000000:
      if self.file_type == self.FILE_TYPE_SEPARATE:
        file_selector = cache_address & 0x0fffffff
        self.filename = 'f_{0:06x}'.format(file_selector)

      elif self.file_type in self._BLOCK_DATA_FILE_TYPES:
        file_selector = (cache_address & 0x00ff0000) >> 16
        self.filename = 'data_{0:d}'.format(file_selector)

        file_block_size = self._FILE_TYPE_BLOCK_SIZES[self.file_type]
        self.block_number = cache_address & 0x0000ffff
        self.block_size = (cache_address & 0x03000000) >> 24
        self.block_size *= file_block_size
        self.block_offset = 8192 + (self.block_number * file_block_size)


class CacheEntry(object):
  """Chrome cache entry.

  Attributes:
    creation_time (int): creation time, in number of microseconds since
        January 1, 1601, 00:00:00 UTC.
    hash (int): super fast hash of the key.
    key (bytes): key.
    next (int): cache address of the next cache entry.
    original_url (str): original URL derived from the key.
    rankings_node (int): cache address of the rankings node.
  """

  def __init__(self):
    """Initializes a cache entry."""
    super(CacheEntry, self).__init__()
    self.creation_time = None
    self.hash = None
    self.key = None
    self.next = None
    self.original_url = None
    self.rankings_node = None


class ChromeCacheIndexFileParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Chrome cache index file parser.

  Attributes:
    creation_time (int): creation time, in number of microseconds since January
        1, 1601, 00:00:00 UTC.
    index_table (list[CacheAddress]): the cache addresses which are stored in
        the index file.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'chrome_cache.yaml')

  def __init__(self):
    """Initializes an index file."""
    super(ChromeCacheIndexFileParser, self).__init__()
    self.creation_time = None
    self.index_table = []

  def _ParseFileHeader(self, file_object):
    """Parses the file header.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: if the file header cannot be read.
    """
    file_header_map = self._GetDataTypeMap('chrome_cache_index_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse index file header with error: {0!s}'.format(
              exception))

    format_version = '{0:d}.{1:d}'.format(
        file_header.major_version, file_header.minor_version)
    if format_version not in ('2.0', '2.1', '3.0'):
      raise errors.ParseError(
          'Unsupported index file format version: {0:s}'.format(format_version))
    self.creation_time = file_header.creation_time

  def _ParseIndexTable(self, file_object):
    """Parses the index table.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: if the index table cannot be read.
    """
    cache_address_map = self._GetDataTypeMap('uint32le')
    file_offset = file_object.get_offset()

    cache_address_data = file_object.read(4)

    while len(cache_address_data) == 4:
      try:
        value = self._ReadStructureFromByteStream(
            cache_address_data, file_offset, cache_address_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to map cache address at offset: 0x{0:08x} with error: '
            '{1!s}').format(file_offset, exception))

      if value:
        cache_address = CacheAddress(value)
        self.index_table.append(cache_address)

      file_offset += 4

      cache_address_data = file_object.read(4)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: when the file cannot be parsed.
    """
    try:
      self._ParseFileHeader(file_object)
    except errors.ParseError as exception:
      raise errors.ParseError(
          'Unable to parse index file header with error: {0!s}'.format(
              exception))
    # Skip over the LRU data, which is 112 bytes in size.
    file_object.seek(112, os.SEEK_CUR)
    self._ParseIndexTable(file_object)


class ChromeCacheDataBlockFileParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Chrome cache data block file parser."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'chrome_cache.yaml')

  def _ParseFileHeader(self, file_object):
    """Parses the file header.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: if the file header cannot be read.
    """
    file_header_map = self._GetDataTypeMap(
        'chrome_cache_data_block_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse data block file header with error: {0!s}'.format(
              exception))

    format_version = '{0:d}.{1:d}'.format(
        file_header.major_version, file_header.minor_version)
    if format_version not in ('2.0', '2.1'):
      raise errors.ParseError(
          'Unsupported data block file format version: {0:s}'.format(
              format_version))

    if file_header.block_size not in (256, 1024, 4096):
      raise errors.ParseError(
          'Unsupported data block file block size: {0:d}'.format(
              file_header.block_size))

  def ParseCacheEntry(self, file_object, block_offset):
    """Parses a cache entry.

    Args:
      file_object (dfvfs.FileIO): a file-like object to read from.
      block_offset (int): block offset of the cache entry.

    Returns:
      CacheEntry: cache entry.

    Raises:
      ParseError: if the cache entry cannot be read.
    """
    cache_entry_map = self._GetDataTypeMap('chrome_cache_entry')

    try:
      cache_entry, _ = self._ReadStructureFromFileObject(
          file_object, block_offset, cache_entry_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse cache entry at offset: 0x{0:08x} with error: '
          '{1!s}').format(block_offset, exception))

    cache_entry_object = CacheEntry()

    cache_entry_object.hash = cache_entry.hash
    cache_entry_object.next = CacheAddress(cache_entry.next_address)
    cache_entry_object.rankings_node = CacheAddress(
        cache_entry.rankings_node_address)
    cache_entry_object.creation_time = cache_entry.creation_time

    byte_array = cache_entry.key
    byte_string = bytes(bytearray(byte_array))
    cache_entry_object.key, _, _ = byte_string.partition(b'\x00')

    try:
      cache_entry_object.original_url = cache_entry_object.key.decode('ascii')
    except UnicodeDecodeError as exception:
      raise errors.ParseError(
          'Unable to decode original URL in key with error: {0!s}'.format(
              exception))

    return cache_entry_object

  # pylint: disable=unused-argument
  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: when the file cannot be parsed.
    """
    self._ParseFileHeader(file_object)


class ChromeCacheEntryEventData(events.EventData):
  """Chrome Cache event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the cache entry.
    original_url (str): original URL.
  """

  DATA_TYPE = 'chrome:cache:entry'

  def __init__(self):
    """Initializes event data."""
    super(ChromeCacheEntryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.original_url = None


class ChromeCacheParser(interface.FileEntryParser):
  """Parses Chrome Cache files."""

  NAME = 'chrome_cache'
  DATA_FORMAT = 'Google Chrome or Chromium Cache file'

  def __init__(self):
    """Initializes a Chrome Cache files parser."""
    super(ChromeCacheParser, self).__init__()
    self._data_block_file_parser = ChromeCacheDataBlockFileParser()

  def _ParseCacheEntries(self, parser_mediator, index_table, data_block_files):
    """Parses Chrome Cache file entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      index_table (list[CacheAddress]): the cache addresses which are stored in
          the index file.
      data_block_files (dict[str: file]): look up table for the data block
          file-like object handles.
    """
    # Parse the cache entries in the data block files.
    for cache_address in index_table:
      cache_address_chain_length = 0
      while cache_address.value != 0:
        if cache_address_chain_length >= 64:
          parser_mediator.ProduceExtractionWarning(
              'Maximum allowed cache address chain length reached.')
          break

        data_block_file_object = data_block_files.get(
            cache_address.filename, None)
        if not data_block_file_object:
          message = 'Cache address: 0x{0:08x} missing data file.'.format(
              cache_address.value)
          parser_mediator.ProduceExtractionWarning(message)
          break

        try:
          cache_entry = self._data_block_file_parser.ParseCacheEntry(
              data_block_file_object, cache_address.block_offset)
        except (IOError, errors.ParseError) as exception:
          parser_mediator.ProduceExtractionWarning(
              'Unable to parse cache entry with error: {0!s}'.format(
                  exception))
          break

        event_data = ChromeCacheEntryEventData()
        event_data.creation_time = dfdatetime_webkit_time.WebKitTime(
            timestamp=cache_entry.creation_time)

        # In Chrome Cache v3, doublekey-ing cache entries was introduced
        # This shows up as r"_dk_{domain}( {domain})* {url}"
        # https://chromium.googlesource.com/chromium/src/+/
        # 95faad3cfd90169f0a267e979c36e3348476a948/net/http/http_cache.cc#427
        if "_dk_" in cache_entry.original_url[:20]:
          parsed_url = cache_entry.original_url.strip().rsplit(' ', 1)[-1]
          event_data.original_url = parsed_url
        else:
          event_data.original_url = cache_entry.original_url

        parser_mediator.ProduceEventData(event_data)

        cache_address = cache_entry.next
        cache_address_chain_length += 1

  def _ParseIndexTable(
      self, parser_mediator, file_system, file_entry, index_table):
    """Parses a Chrome Cache index table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_system (dfvfs.FileSystem): file system.
      file_entry (dfvfs.FileEntry): file entry.
      index_table (list[CacheAddress]): the cache addresses which are stored in
          the index file.
    """
    # Build a lookup table for the data block files.
    path_segments = file_system.SplitPath(file_entry.path_spec.location)

    data_block_files = {}
    for cache_address in index_table:
      if cache_address.filename not in data_block_files:
        # Remove the previous filename from the path segments list and
        # add one of the data block files.
        path_segments.pop()
        path_segments.append(cache_address.filename)

        # We need to pass only used arguments to the path specification
        # factory otherwise it will raise.
        kwargs = {}
        if file_entry.path_spec.parent:
          kwargs['parent'] = file_entry.path_spec.parent
        kwargs['location'] = file_system.JoinPath(path_segments)

        data_block_file_path_spec = path_spec_factory.Factory.NewPathSpec(
            file_entry.path_spec.TYPE_INDICATOR, **kwargs)

        try:
          data_block_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
              data_block_file_path_spec)
        except RuntimeError as exception:
          message = (
              'Unable to open data block file: {0:s} with error: '
              '{1!s}'.format(kwargs['location'], exception))
          parser_mediator.ProduceExtractionWarning(message)
          data_block_file_entry = None

        if not data_block_file_entry:
          message = 'Missing data block file: {0:s}'.format(
              cache_address.filename)
          parser_mediator.ProduceExtractionWarning(message)
          data_block_file_object = None

        else:
          data_block_file_object = data_block_file_entry.GetFileObject()

          try:
            self._data_block_file_parser.ParseFileObject(
                parser_mediator, data_block_file_object)
          except (IOError, errors.ParseError) as exception:
            message = (
                'Unable to parse data block file: {0:s} with error: '
                '{1!s}').format(cache_address.filename, exception)
            parser_mediator.ProduceExtractionWarning(message)
            data_block_file_object = None
        data_block_files[cache_address.filename] = data_block_file_object
    self._ParseCacheEntries(parser_mediator, index_table, data_block_files)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\xc3\xca\x03\xc1', offset=0)
    return format_specification

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses Chrome Cache files.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): file entry.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    index_file_parser = ChromeCacheIndexFileParser()

    file_object = file_entry.GetFileObject()
    if not file_object:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse index file {1:s}'.format(
              self.NAME, display_name))

    try:
      index_file_parser.ParseFileObject(parser_mediator, file_object)
    except (IOError, errors.ParseError) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse index file {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))

    # TODO: create event based on index file creation time.

    file_system = file_entry.GetFileSystem()
    self._ParseIndexTable(
        parser_mediator, file_system, file_entry, index_file_parser.index_table)


manager.ParsersManager.RegisterParser(ChromeCacheParser)
