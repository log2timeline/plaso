# -*- coding: utf-8 -*-
"""Parser for Google Chrome and Chromium Cache files."""

import os

import construct

from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.path import factory as path_spec_factory

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class CacheAddress(object):
  """Class that contains a cache address."""
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
    """Initializes the cache address object.

    Args:
      cache_address: the cache address value.
    """
    super(CacheAddress, self).__init__()
    self.block_number = None
    self.block_offset = None
    self.block_size = None
    self.filename = None
    self.value = cache_address

    if cache_address & 0x80000000:
      self.is_initialized = u'True'
    else:
      self.is_initialized = u'False'

    self.file_type = (cache_address & 0x70000000) >> 28
    if not cache_address == 0x00000000:
      if self.file_type == self.FILE_TYPE_SEPARATE:
        file_selector = cache_address & 0x0fffffff
        self.filename = u'f_{0:06x}'.format(file_selector)

      elif self.file_type in self._BLOCK_DATA_FILE_TYPES:
        file_selector = (cache_address & 0x00ff0000) >> 16
        self.filename = u'data_{0:d}'.format(file_selector)

        file_block_size = self._FILE_TYPE_BLOCK_SIZES[self.file_type]
        self.block_number = cache_address & 0x0000ffff
        self.block_size = (cache_address & 0x03000000) >> 24
        self.block_size *= file_block_size
        self.block_offset = 8192 + (self.block_number * file_block_size)


class CacheEntry(object):
  """Class that contains a cache entry."""

  def __init__(self):
    """Initializes the cache entry object."""
    super(CacheEntry, self).__init__()
    self.creation_time = None
    self.hash = None
    self.key = None
    self.next = None
    self.rankings_node = None


class IndexFile(object):
  """Class that contains an index file."""

  SIGNATURE = 0xc103cac3

  _FILE_HEADER = construct.Struct(
      u'chrome_cache_index_file_header',
      construct.ULInt32(u'signature'),
      construct.ULInt16(u'minor_version'),
      construct.ULInt16(u'major_version'),
      construct.ULInt32(u'number_of_entries'),
      construct.ULInt32(u'stored_data_size'),
      construct.ULInt32(u'last_created_file_number'),
      construct.ULInt32(u'unknown1'),
      construct.ULInt32(u'unknown2'),
      construct.ULInt32(u'table_size'),
      construct.ULInt32(u'unknown3'),
      construct.ULInt32(u'unknown4'),
      construct.ULInt64(u'creation_time'),
      construct.Padding(208))

  def __init__(self):
    """Initializes the index file object."""
    super(IndexFile, self).__init__()
    self._file_object = None
    self.creation_time = None
    self.version = None
    self.index_table = []

  def _ReadFileHeader(self):
    """Reads the file header.

    Raises:
      IOError: if the file header cannot be read.
    """
    self._file_object.seek(0, os.SEEK_SET)

    try:
      file_header = self._FILE_HEADER.parse_stream(self._file_object)
    except construct.FieldError as exception:
      raise IOError(u'Unable to parse file header with error: {0:s}'.format(
          exception))

    signature = file_header.get(u'signature')

    if signature != self.SIGNATURE:
      raise IOError(u'Unsupported index file signature')

    self.version = u'{0:d}.{1:d}'.format(
        file_header.get(u'major_version'),
        file_header.get(u'minor_version'))

    if self.version not in [u'2.0', u'2.1']:
      raise IOError(u'Unsupported index file version: {0:s}'.format(
          self.version))

    self.creation_time = file_header.get(u'creation_time')

  def _ReadIndexTable(self):
    """Reads the index table."""
    cache_address_data = self._file_object.read(4)

    while len(cache_address_data) == 4:
      value = construct.ULInt32(u'cache_address').parse(cache_address_data)

      if value:
        cache_address = CacheAddress(value)
        self.index_table.append(cache_address)

      cache_address_data = self._file_object.read(4)

  def Close(self):
    """Closes the index file."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

  def Open(self, file_object):
    """Opens the index file.

    Args:
      file_object: the file object.
    """
    self._file_object = file_object
    self._ReadFileHeader()
    # Skip over the LRU data, which is 112 bytes in size.
    self._file_object.seek(112, os.SEEK_CUR)
    self._ReadIndexTable()


class DataBlockFile(object):
  """Class that contains a data block file."""

  SIGNATURE = 0xc104cac3

  _FILE_HEADER = construct.Struct(
      u'chrome_cache_data_file_header',
      construct.ULInt32(u'signature'),
      construct.ULInt16(u'minor_version'),
      construct.ULInt16(u'major_version'),
      construct.ULInt16(u'file_number'),
      construct.ULInt16(u'next_file_number'),
      construct.ULInt32(u'block_size'),
      construct.ULInt32(u'number_of_entries'),
      construct.ULInt32(u'maximum_number_of_entries'),
      construct.Array(4, construct.ULInt32(u'emtpy')),
      construct.Array(4, construct.ULInt32(u'hints')),
      construct.ULInt32(u'updating'),
      construct.Array(5, construct.ULInt32(u'user')))

  _CACHE_ENTRY = construct.Struct(
      u'chrome_cache_entry',
      construct.ULInt32(u'hash'),
      construct.ULInt32(u'next_address'),
      construct.ULInt32(u'rankings_node_address'),
      construct.ULInt32(u'reuse_count'),
      construct.ULInt32(u'refetch_count'),
      construct.ULInt32(u'state'),
      construct.ULInt64(u'creation_time'),
      construct.ULInt32(u'key_size'),
      construct.ULInt32(u'long_key_address'),
      construct.Array(4, construct.ULInt32(u'data_stream_sizes')),
      construct.Array(4, construct.ULInt32(u'data_stream_addresses')),
      construct.ULInt32(u'flags'),
      construct.Padding(16),
      construct.ULInt32(u'self_hash'),
      construct.Array(160, construct.UBInt8(u'key')))

  def __init__(self):
    """Initializes the data block file object."""
    super(DataBlockFile, self).__init__()
    self._file_object = None
    self.creation_time = None
    self.block_size = None
    self.number_of_entries = None
    self.version = None

  def _ReadFileHeader(self):
    """Reads the file header.

    Raises:
      IOError: if the file header cannot be read.
    """
    self._file_object.seek(0, os.SEEK_SET)

    try:
      file_header = self._FILE_HEADER.parse_stream(self._file_object)
    except construct.FieldError as exception:
      raise IOError(u'Unable to parse file header with error: {0:s}'.format(
          exception))

    signature = file_header.get(u'signature')

    if signature != self.SIGNATURE:
      raise IOError(u'Unsupported data block file signature')

    self.version = u'{0:d}.{1:d}'.format(
        file_header.get(u'major_version'),
        file_header.get(u'minor_version'))

    if self.version not in [u'2.0', u'2.1']:
      raise IOError(u'Unsupported data block file version: {0:s}'.format(
          self.version))

    self.block_size = file_header.get(u'block_size')
    self.number_of_entries = file_header.get(u'number_of_entries')

  def ReadCacheEntry(self, block_offset):
    """Reads a cache entry.

    Args:
      block_offset: The block offset of the cache entry.

    Returns:
      A cache entry (instance of CacheEntry).
    """
    self._file_object.seek(block_offset, os.SEEK_SET)

    try:
      cache_entry_struct = self._CACHE_ENTRY.parse_stream(self._file_object)
    except construct.FieldError as exception:
      raise IOError(u'Unable to parse cache entry with error: {0:s}'.format(
          exception))

    cache_entry = CacheEntry()

    cache_entry.hash = cache_entry_struct.get(u'hash')

    cache_entry.next = CacheAddress(cache_entry_struct.get(u'next_address'))
    cache_entry.rankings_node = CacheAddress(cache_entry_struct.get(
        u'rankings_node_address'))

    cache_entry.creation_time = cache_entry_struct.get(u'creation_time')

    byte_array = cache_entry_struct.get(u'key')
    string = u''.join(map(chr, byte_array))
    cache_entry.key, _, _ = string.partition(u'\x00')

    return cache_entry

  def Close(self):
    """Closes the data block file."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

  def Open(self, file_object):
    """Opens the data block file.

    Args:
      file_object: the file object.
    """
    self._file_object = file_object
    self._ReadFileHeader()


class ChromeCacheEntryEvent(time_events.WebKitTimeEvent):
  """Class that contains a Chrome Cache event."""

  DATA_TYPE = u'chrome:cache:entry'

  def __init__(self, cache_entry):
    """Initializes the event object.

    Args:
      cache_entry: the cache entry (instance of CacheEntry).
    """
    super(ChromeCacheEntryEvent, self).__init__(
        cache_entry.creation_time, eventdata.EventTimestamp.CREATION_TIME)
    self.original_url = cache_entry.key


class ChromeCacheParser(interface.BaseParser):
  """Parses Chrome Cache files."""

  NAME = u'chrome_cache'
  DESCRIPTION = u'Parser for Chrome Cache files.'

  def _ParseCacheEntries(self, parser_mediator, index_file, data_block_files):
    """Parses Chrome Cache file entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      index_file: A Chrome cache index file object (instance of IndexFile).
      data_block_files: A dictionary containing the data block files lookup
                        table which contains data block file objects (instances
                        of DataBlockFile).
    """
    # Parse the cache entries in the data block files.
    for cache_address in index_file.index_table:
      cache_address_chain_length = 0
      while cache_address.value != 0x00000000:
        if cache_address_chain_length >= 64:
          parser_mediator.ProduceParseError(
              u'Maximum allowed cache address chain length reached.')
          break

        data_file = data_block_files.get(cache_address.filename, None)
        if not data_file:
          message = u'Cache address: 0x{0:08x} missing data file.'.format(
              cache_address.value)
          parser_mediator.ProduceParseError(message)
          break

        try:
          cache_entry = data_file.ReadCacheEntry(cache_address.block_offset)
        except (IOError, UnicodeDecodeError) as exception:
          parser_mediator.ProduceParseError(
              u'Unable to parse cache entry with error: {0:s}'.format(
                  exception))
          break

        event_object = ChromeCacheEntryEvent(cache_entry)
        parser_mediator.ProduceEvent(event_object)

        cache_address = cache_entry.next
        cache_address_chain_length += 1

  def Parse(self, parser_mediator, **kwargs):
    """Parses Chrome Cache files.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    display_name = parser_mediator.GetDisplayName()
    file_object = parser_mediator.GetFileObject()

    index_file = IndexFile()
    try:
      index_file.Open(file_object)
    except IOError as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse index file {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    file_entry = parser_mediator.GetFileEntry()
    file_system = file_entry.GetFileSystem()

    try:
      self.ParseIndexFile(
          parser_mediator, file_system, file_entry, index_file, **kwargs)
    finally:
      index_file.Close()

  def ParseIndexFile(
      self, parser_mediator, file_system, file_entry, index_file, **kwargs):
    """Parses a Chrome Cache index file object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_system: The file system object (instance of dfvfs.FileSystem).
      file_entry: The file entry object (instance of dfvfs.FileEntry).
      index_file: An index file object (instance of IndexFile)
    """
    # Build a lookup table for the data block files.
    path_segments = file_system.SplitPath(file_entry.path_spec.location)

    data_block_files = {}
    for cache_address in index_file.index_table:
      if cache_address.filename not in data_block_files:
        # Remove the previous filename from the path segments list and
        # add one of the data block file.
        path_segments.pop()
        path_segments.append(cache_address.filename)

        # We need to pass only used arguments to the path specification
        # factory otherwise it will raise.
        kwargs = {}
        if file_entry.path_spec.parent:
          kwargs[u'parent'] = file_entry.path_spec.parent
        kwargs[u'location'] = file_system.JoinPath(path_segments)

        data_block_file_path_spec = path_spec_factory.Factory.NewPathSpec(
            file_entry.path_spec.TYPE_INDICATOR, **kwargs)

        try:
          data_block_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
              data_block_file_path_spec)
        except RuntimeError as exception:
          message = (
              u'Unable to open data block file: {0:s} with error: '
              u'{1:s}'.format(kwargs[u'location'], exception))
          parser_mediator.ProduceParseError(message)
          data_block_file_entry = None

        if not data_block_file_entry:
          message = u'Missing data block file: {0:s}'.format(
              cache_address.filename)
          parser_mediator.ProduceParseError(message)
          data_block_file = None

        else:
          data_block_file_object = data_block_file_entry.GetFileObject()
          data_block_file = DataBlockFile()

          try:
            data_block_file.Open(data_block_file_object)
          except IOError as exception:
            message = (
                u'Unable to open data block file: {0:s} with error: '
                u'{1:s}').format(cache_address.filename, exception)
            parser_mediator.ProduceParseError(message)
            data_block_file = None

        data_block_files[cache_address.filename] = data_block_file

    try:
      self._ParseCacheEntries(parser_mediator, index_file, data_block_files)
    finally:
      for data_block_file in data_block_files.itervalues():
        if data_block_file:
          data_block_file.Close()


manager.ParsersManager.RegisterParser(ChromeCacheParser)
