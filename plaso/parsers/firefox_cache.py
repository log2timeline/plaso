# -*- coding: utf-8 -*-
"""Implements a parser for Firefox cache 1 and 2 files."""

import collections
import re
import os

from dfdatetime import posix_time as dfdatetime_posix_time

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class FirefoxCacheEventData(events.EventData):
  """Firefox cache event data.

  Attributes:
    data_size (int): size of the cached data.
    expiration_time (dfdatetime.DateTimeValues): date and time the cache
        entry expires.
    fetch_count (int): number of times the cache entry was fetched.
    frequency (int): ???
    info_size (int): size of the metadata.
    last_fetched_time (dfdatetime.DateTimeValues): date and time the cache
        entry was last fetched.
    last_modified_time (dfdatetime.DateTimeValues): date and time the cache
        entry was last modified.
    location (str): ???
    request_method (str): HTTP request method.
    request_size (int): HTTP request byte size.
    response_code (int): HTTP response code.
    url (str): URL of original content.
    version (str): cache format version.
  """

  DATA_TYPE = 'firefox:cache:record'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.data_size = None
    self.expiration_time = None
    self.fetch_count = None
    self.frequency = None
    self.info_size = None
    self.last_fetched_time = None
    self.last_modified_time = None
    self.location = None
    self.request_method = None
    self.request_size = None
    self.response_code = None
    self.url = None
    self.version = None


class BaseFirefoxCacheParser(interface.FileObjectParser):
  """Parses Firefox cache files."""

  # pylint: disable=abstract-method

  _MAXIMUM_URL_LENGTH = 65536

  _REQUEST_METHODS = frozenset([
      'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST',
      'PUT', 'TRACE'])

  _CACHE_ENTRY_HEADER_SIZE = 36

  def _ParseHTTPHeaders(self, http_headers_data, offset, display_name):
    """Extract relevant information from HTTP header.

    Args:
      http_headers_data (bytes): HTTP headers data.
      offset (int): offset of the cache record, relative to the start of
          the Firefox cache file.
      display_name (str): display name of the Firefox cache file.

    Returns:
      tuple: containing:

        str: HTTP request method or None if the value cannot be extracted.
        str: HTTP response code or None if the value cannot be extracted.
    """
    header_string = http_headers_data.decode('ascii', errors='replace')

    try:
      http_header_start = header_string.index('request-method')
    except ValueError:
      logger.debug('No request method in header: "{0:s}"'.format(header_string))
      return None, None

    # HTTP request and response headers.
    http_headers = header_string[http_header_start::]

    header_parts = http_headers.split('\x00')

    # TODO: check len(header_parts).
    request_method = header_parts[1]

    if request_method not in self._REQUEST_METHODS:
      logger.debug((
          '[{0:s}] {1:s}:{2:d}: Unknown HTTP method \'{3:s}\'. Response '
          'headers: \'{4:s}\'').format(
              self.NAME, display_name, offset, request_method, header_string))

    try:
      response_head_start = http_headers.index('response-head')
    except ValueError:
      logger.debug('No response head in header: "{0:s}"'.format(header_string))
      return request_method, None

    # HTTP response headers.
    response_head = http_headers[response_head_start::]

    response_head_parts = response_head.split('\x00')

    # Response code, followed by other response header key-value pairs,
    # separated by newline.
    # TODO: check len(response_head_parts).
    response_head_text = response_head_parts[1]
    response_head_text_parts = response_head_text.split('\r\n')

    # The first line contains response code.
    # TODO: check len(response_head_text_parts).
    response_code = response_head_text_parts[0]

    if not response_code.startswith('HTTP'):
      logger.debug((
          '[{0:s}] {1:s}:{2:d}: Could not determine HTTP response code. '
          'Response headers: \'{3:s}\'.').format(
              self.NAME, display_name, offset, header_string))

    return request_method, response_code


class FirefoxCacheParser(
    BaseFirefoxCacheParser, dtfabric_helper.DtFabricHelper):
  """Parses Firefox cache version 1 files (Firefox 31 or earlier)."""

  NAME = 'firefox_cache'
  DATA_FORMAT = 'Mozilla Firefox Cache version 1 file (version 31 or earlier)'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'firefox_cache.yaml')

  # Initial size of Firefox 4 and later cache files.
  _INITIAL_CACHE_FILE_SIZE = 4 * 1024 * 1024

  # Smallest possible block size in Firefox cache files.
  _MINIMUM_BLOCK_SIZE = 256

  # Name of a cache data file that contains metadata.
  _CACHE_FILENAME_RE = re.compile(r'^[0-9A-Fa-f]{5}m[0-9]{2}$')

  FIREFOX_CACHE_CONFIG = collections.namedtuple(
      'firefox_cache_config',
      'block_size first_record_offset')

  def _GetFirefoxConfig(self, file_object, display_name):
    """Determine cache file block size.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      display_name (str): display name.

    Returns:
      firefox_cache_config: namedtuple containing the block size and first
          record offset.

    Raises:
      WrongParser: if no valid cache record could be found.
    """
    # There ought to be a valid record within the first 4 MiB. We use this
    # limit to prevent reading large invalid files.
    to_read = min(file_object.get_size(), self._INITIAL_CACHE_FILE_SIZE)

    while file_object.get_offset() < to_read:
      offset = file_object.get_offset()

      try:
        cache_entry = self._ParseCacheEntry(
            None, file_object, display_name, self._MINIMUM_BLOCK_SIZE)

        # We have not yet determined the block size, so we use the smallest
        # possible size.
        record_size = (
            self._CACHE_ENTRY_HEADER_SIZE + cache_entry.request_size +
            cache_entry.information_size)

        if record_size >= 4096:
          # _CACHE_003_
          block_size = 4096
        elif record_size >= 1024:
          # _CACHE_002_
          block_size = 1024
        else:
          # _CACHE_001_
          block_size = 256

        return self.FIREFOX_CACHE_CONFIG(block_size, offset)

      except IOError:
        logger.debug('[{0:s}] {1:s}:{2:d}: Invalid record.'.format(
            self.NAME, display_name, offset))

    raise errors.WrongParser(
        'Could not find a valid cache record. Not a Firefox cache file.')

  def _ParseCacheEntry(
      self, parser_mediator, file_object, display_name, block_size):
    """Parses a cache entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.
      display_name (str): display name.
      block_size (int): block size.

    Returns:
      firefox_cache1_entry_header: cache record header structure.

    Raises:
      IOError: if the cache record header cannot be validated.
      OSError: if the cache record header cannot be validated.
      ParseError: if the cache record header cannot be parsed.
    """
    file_offset = file_object.get_offset()

    # Seeing that this parser tries to read each block for a possible
    # cache entry, we read the fixed-size values first.
    cache_entry_header_map = self._GetDataTypeMap('firefox_cache1_entry_header')

    try:
      cache_entry_header, header_data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, cache_entry_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse Firefox cache entry header with error: {0!s}'.format(
              exception))

    if not self._ValidateCacheEntryHeader(cache_entry_header):
      # Skip to the next block potentially containing a cache entry.
      file_offset = block_size - header_data_size
      file_object.seek(file_offset, os.SEEK_CUR)
      raise IOError('Not a valid Firefox cache record.')

    file_offset += header_data_size
    body_data_size = (
        cache_entry_header.request_size + cache_entry_header.information_size)

    cache_entry_body_data = self._ReadData(
        file_object, file_offset, body_data_size)

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'firefox_cache1_entry_header': cache_entry_header})

    cache_entry_body_map = self._GetDataTypeMap('firefox_cache1_entry_body')

    try:
      cache_entry_body = self._ReadStructureFromByteStream(
          cache_entry_body_data, file_offset, cache_entry_body_map,
          context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map cache entry body data at offset: 0x{0:08x} with '
          'error: {1!s}').format(file_offset, exception))

    file_offset += cache_entry_header.request_size

    request_method, response_code = self._ParseHTTPHeaders(
        cache_entry_body.information, file_offset, display_name)

    # A request can span multiple blocks, so we use modulo.
    cache_entry_data_size = header_data_size + body_data_size
    _, remaining_data_size = divmod(cache_entry_data_size, block_size)
    if remaining_data_size > 0:
      file_object.seek(block_size - remaining_data_size, os.SEEK_CUR)

    if parser_mediator:
      event_data = FirefoxCacheEventData()
      event_data.data_size = cache_entry_header.cached_data_size
      event_data.fetch_count = cache_entry_header.fetch_count
      event_data.info_size = cache_entry_header.information_size
      event_data.last_fetched_time = dfdatetime_posix_time.PosixTime(
          timestamp=cache_entry_header.last_fetched_time)
      event_data.location = cache_entry_header.location
      event_data.request_method = request_method
      event_data.request_size = cache_entry_header.request_size
      event_data.response_code = response_code
      event_data.url = cache_entry_body.request
      event_data.version = '{0:d}.{1:d}'.format(
          cache_entry_header.major_format_version,
          cache_entry_header.minor_format_version)

      if cache_entry_header.last_modified_time:
        event_data.last_modified_time = dfdatetime_posix_time.PosixTime(
            timestamp=cache_entry_header.last_modified_time)

      if cache_entry_header.expiration_time:
        event_data.expiration_time = dfdatetime_posix_time.PosixTime(
            timestamp=cache_entry_header.expiration_time)

      parser_mediator.ProduceEventData(event_data)

    return cache_entry_header

  def _ValidateCacheEntryHeader(self, cache_entry_header):
    """Determines whether the values in the cache entry header are valid.

    Args:
      cache_entry_header (firefox_cache1_entry_header): cache entry header.

    Returns:
      bool: True if the cache entry header is valid.
    """
    return (cache_entry_header.request_size > 0 and
            cache_entry_header.request_size < self._MAXIMUM_URL_LENGTH and
            cache_entry_header.major_format_version == 1 and
            cache_entry_header.last_fetched_time > 0 and
            cache_entry_header.fetch_count > 0)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Firefox cache file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()

    if (not self._CACHE_FILENAME_RE.match(filename) and
        not filename.startswith('_CACHE_00')):
      raise errors.WrongParser('Not a Firefox cache1 file.')

    display_name = parser_mediator.GetDisplayName()
    firefox_config = self._GetFirefoxConfig(file_object, display_name)

    file_object.seek(firefox_config.first_record_offset)

    while file_object.get_offset() < file_object.get_size():
      try:
        self._ParseCacheEntry(
            parser_mediator, file_object, display_name,
            firefox_config.block_size)

      except IOError:
        file_offset = file_object.get_offset() - self._MINIMUM_BLOCK_SIZE
        logger.debug((
            '[{0:s}] Invalid cache record in file: {1:s} at offset: '
            '{2:d}.').format(self.NAME, display_name, file_offset))


class FirefoxCache2Parser(
    BaseFirefoxCacheParser, dtfabric_helper.DtFabricHelper):
  """Parses Firefox cache version 2 files (Firefox 32 or later)."""

  NAME = 'firefox_cache2'
  DATA_FORMAT = 'Mozilla Firefox Cache version 2 file (version 32 or later)'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'firefox_cache.yaml')

  # Cache version 2 filenames are SHA-1 hex digests.
  _CACHE_FILENAME_RE = re.compile(r'^[0-9A-Fa-f]{40}$')

  _CHUNK_SIZE = 512 * 1024

  _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

  # The file needs to be at least 36 bytes in size for it to contain
  # a cache2 file metadata header and a 4-byte offset that points to its
  # location in the file.
  _MINIMUM_FILE_SIZE = 36

  def _GetCacheFileMetadataHeaderOffset(self, file_object):
    """Determines the offset of the cache file metadata header.

    This method is inspired by the work of James Habben:
    https://github.com/JamesHabben/FirefoxCache2

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      int: offset of the file cache metadata header relative to the start
          of the file.

    Raises:
      WrongParser: if the size of the cache file metadata cannot be
          determined.
    """
    file_object.seek(-4, os.SEEK_END)
    file_offset = file_object.tell()

    metadata_size_map = self._GetDataTypeMap('uint32be')

    try:
      metadata_size, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, metadata_size_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse cache file metadata size with error: {0!s}'.format(
              exception))

    # Firefox splits the content into chunks.
    number_of_chunks, remainder = divmod(metadata_size, self._CHUNK_SIZE)
    if remainder != 0:
      number_of_chunks += 1

    # Each chunk in the cached record is padded with two bytes.
    # Skip the first 4 bytes which contains a hash value of the cached content.
    return metadata_size + (number_of_chunks * 2) + 4

  def _ValidateCacheFileMetadataHeader(self, cache_file_metadata_header):
    """Determines whether the cache file metadata header is valid.

    Args:
      cache_file_metadata_header (firefox_cache2_file_metadata_header): cache
          file metadata header.

    Returns:
      bool: True if the cache file metadata header is valid.
    """
    return (cache_file_metadata_header.key_size > 0 and
            cache_file_metadata_header.key_size < self._MAXIMUM_URL_LENGTH and
            cache_file_metadata_header.format_version in (1, 2, 3) and
            cache_file_metadata_header.last_fetched_time > 0 and
            cache_file_metadata_header.fetch_count > 0)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Firefox cache file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()
    if not self._CACHE_FILENAME_RE.match(filename):
      raise errors.WrongParser('Not a Firefox cache2 file.')

    file_offset = self._GetCacheFileMetadataHeaderOffset(file_object)
    file_metadata_header_map = self._GetDataTypeMap(
        'firefox_cache2_file_metadata_header')

    try:
      file_metadata_header, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, file_metadata_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Unable to parse Firefox cache2 file metadata header with error: '
          '{0!s}').format(exception))

    if not self._ValidateCacheFileMetadataHeader(file_metadata_header):
      raise errors.WrongParser('Not a valid Firefox cache2 record.')

    if file_metadata_header.format_version >= 2:
      file_object.seek(4, os.SEEK_CUR)

    url = file_object.read(file_metadata_header.key_size)

    # Note that _MAXIMUM_FILE_SIZE prevents this read to become too large.
    http_headers_data = file_object.read()

    display_name = parser_mediator.GetDisplayName()
    request_method, response_code = self._ParseHTTPHeaders(
        http_headers_data[:-4], file_offset, display_name)

    event_data = FirefoxCacheEventData()
    event_data.fetch_count = file_metadata_header.fetch_count
    event_data.frequency = file_metadata_header.frequency
    event_data.last_fetched_time = dfdatetime_posix_time.PosixTime(
        timestamp=file_metadata_header.last_fetched_time)
    event_data.request_method = request_method
    event_data.request_size = file_metadata_header.key_size
    event_data.response_code = response_code
    event_data.version = '2'
    event_data.url = url.decode('ascii', errors='replace')

    if file_metadata_header.last_modified_time:
      event_data.last_modified_time = dfdatetime_posix_time.PosixTime(
          timestamp=file_metadata_header.last_modified_time)

    if file_metadata_header.expiration_time:
      event_data.expiration_time = dfdatetime_posix_time.PosixTime(
          timestamp=file_metadata_header.expiration_time)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParsers([
    FirefoxCacheParser, FirefoxCache2Parser])
