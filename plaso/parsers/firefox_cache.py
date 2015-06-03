# -*- coding: utf-8 -*-
"""Implements a parser for Firefox cache 1 and 2 files."""

import collections
import logging
import os

import construct
import pyparsing

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Petter Bjelland (petter.bjelland@gmail.com)'


class FirefoxCacheEvent(time_events.PosixTimeEvent):
  """Convenience class for a Firefox cache record event."""

  DATA_TYPE = u'firefox:cache:record'

  def __init__(self, timestamp, timestamp_type, cache_record_values):
    """Initializes the event object.

    Args:
      timestamp: The POSIX timestamp value.
      timestamp_description: A description string for the timestamp value.
      cache_record_values: A dictionary object containing the cache record
                           values.
    """
    super(FirefoxCacheEvent, self).__init__(timestamp, timestamp_type)

    for key, value in iter(cache_record_values.items()):
      setattr(self, key, value)


class BaseFirefoxCacheParser(interface.SingleFileBaseParser):
  """Parses Firefox cache files."""

  # pylint: disable=abstract-method

  DESCRIPTION = u'Parser for Firefox Cache files.'

  _MAXIMUM_URL_LENGTH = 65536

  _REQUEST_METHODS = frozenset([
      u'CONNECT', u'DELETE', u'GET', u'HEAD', u'OPTIONS', u'PATCH', u'POST',
      u'PUT', u'TRACE'])

  def _ParseHTTPHeaders(self, header_data, offset, display_name):
    """Extract relevant information from HTTP header.

    Args:
      header_data: binary string containing the HTTP header data.
      offset: the offset of the cache record.
      display_name: the display name.
    """
    try:
      http_header_start = header_data.index(b'request-method')
    except ValueError:
      logging.debug(u'No request method in header: "{0:s}"'.format(header_data))
      return None, None

    # HTTP request and response headers.
    http_headers = header_data[http_header_start::]

    header_parts = http_headers.split(b'\x00')

    # TODO: check len(header_parts).
    request_method = header_parts[1]

    if request_method not in self._REQUEST_METHODS:
      safe_headers = header_data.decode(u'ascii', errors=u'replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Unknown HTTP method \'{3:s}\'. Response '
          u'headers: \'{4:s}\'').format(
              self.NAME, display_name, offset, request_method, safe_headers))

    try:
      response_head_start = http_headers.index(b'response-head')
    except ValueError:
      logging.debug(u'No response head in header: "{0:s}"'.format(header_data))
      return request_method, None

    # HTTP response headers.
    response_head = http_headers[response_head_start::]

    response_head_parts = response_head.split(b'\x00')

    # Response code, followed by other response header key-value pairs,
    # separated by newline.
    # TODO: check len(response_head_parts).
    response_head_text = response_head_parts[1]
    response_head_text_parts = response_head_text.split(b'\r\n')

    # The first line contains response code.
    # TODO: check len(response_head_text_parts).
    response_code = response_head_text_parts[0]

    if not response_code.startswith(b'HTTP'):
      safe_headers = header_data.decode(u'ascii', errors=u'replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Could not determine HTTP response code. '
          u'Response headers: \'{3:s}\'.').format(
              self.NAME, display_name, offset, safe_headers))

    return request_method, response_code

  def _ValidateCacheRecordHeader(self, cache_record_header):
    """Determines whether the cache record header is valid.

    Args:
      cache_record_header: the cache record header (instance of
                           construct.Struct).

    Returns:
      A boolean value indicating the cache record header is valid.
    """
    return (
        cache_record_header.request_size > 0 and
        cache_record_header.request_size < self._MAXIMUM_URL_LENGTH and
        cache_record_header.major == 1 and
        cache_record_header.last_fetched > 0 and
        cache_record_header.fetch_count > 0)


class FirefoxCacheParser(BaseFirefoxCacheParser):
  """Parses Firefox 32 or later cache files."""

  NAME = u'firefox_cache'

  CACHE_VERSION = 2

  # Cache 2 filenames are SHA-1 hex digests.
  # TODO: change into regexp.
  _CACHE_FILENAME = pyparsing.Word(pyparsing.hexnums, exact=40)

  # The last four bytes of a file gives the size of the cached content.
  _LENGTH = construct.UBInt32(u'length')

  _CACHE_RECORD_HEADER_STRUCT = construct.Struct(
      u'record_header',
      construct.UBInt32(u'major'),
      construct.UBInt32(u'fetch_count'),
      construct.UBInt32(u'last_fetched'),
      construct.UBInt32(u'last_modified'),
      construct.UBInt32(u'frequency'),
      construct.UBInt32(u'expire_time'),
      construct.UBInt32(u'request_size'))

  _CHUNK_SIZE = 512 * 1024

  def _GetStartOfMetadata(self, file_object):
    """Determine the byte offset of the cache record metadata in cache file.

     This method is inspired by the work of James Habben:
     https://github.com/JamesHabben/FirefoxCache2

    Args:
      file_object: The file containing the cache record.
    """
    file_object.seek(-4, os.SEEK_END)

    try:
      length = self._LENGTH.parse_stream(file_object)
    except (IOError, construct.FieldError):
      raise IOError(u'Could not find metadata offset in Firefox cache file.')

    # Firefox splits the content into chunks.
    hash_chunks, remainder = divmod(length, self._CHUNK_SIZE)
    if remainder != 0:
      hash_chunks += 1

    # Each chunk in the cached record is padded with two bytes.
    return length + (hash_chunks * 2)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Firefox cache file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()

    try:
      # Match cache2 filename (SHA-1 hex of cache record key).
      self._CACHE_FILENAME.parseString(file_entry.name)
    except pyparsing.ParseException:
      raise errors.UnableToParseFile(u'Not a Firefox cache2 file.')

    if file_object.get_size() == 0:
      raise errors.UnableToParseFile(u'Empty file.')

    meta_start = self._GetStartOfMetadata(file_object)

    file_object.seek(meta_start, os.SEEK_SET)

    # Skip the first 4 bytes of metadata which contains a hash value of
    # the cached content.
    file_object.seek(4, os.SEEK_CUR)

    try:
      cache_record_header = self._CACHE_RECORD_HEADER_STRUCT.parse_stream(
          file_object)
    except (IOError, construct.FieldError):
      raise errors.UnableToParseFile(u'Not a Firefox cache2 file.')

    if not self._ValidateCacheRecordHeader(cache_record_header):
      raise errors.UnableToParseFile(u'Not a valid Firefox cache2 record.')

    url = file_object.read(cache_record_header.request_size)

    header_data = file_object.read()

    display_name = parser_mediator.GetDisplayName()
    request_method, response_code = self._ParseHTTPHeaders(
        header_data, meta_start, display_name)

    cache_record_values = {
        u'fetch_count': cache_record_header.fetch_count,
        u'frequency': cache_record_header.frequency,
        u'major': cache_record_header.major,
        u'request_method': request_method,
        u'request_size': cache_record_header.request_size,
        u'response_code': response_code,
        u'version': self.CACHE_VERSION,
        u'url': url}

    event_object = FirefoxCacheEvent(
        cache_record_header.last_fetched,
        eventdata.EventTimestamp.LAST_VISITED_TIME, cache_record_values)
    parser_mediator.ProduceEvent(event_object)

    if cache_record_header.last_modified:
      event_object = FirefoxCacheEvent(
          cache_record_header.last_modified,
          eventdata.EventTimestamp.WRITTEN_TIME, cache_record_values)
      parser_mediator.ProduceEvent(event_object)

    if cache_record_header.expire_time:
      event_object = FirefoxCacheEvent(
          cache_record_header.expire_time,
          eventdata.EventTimestamp.EXPIRATION_TIME, cache_record_values)
      parser_mediator.ProduceEvent(event_object)


class FirefoxOldCacheParser(BaseFirefoxCacheParser):
  """Parses Firefox 31 or earlier cache files."""

  NAME = u'firefox_old_cache'

  CACHE_VERSION = 1

  # Initial size of Firefox 4 and later cache files.
  _INITIAL_CACHE_FILE_SIZE = 4 * 1024 * 1024

  # Smallest possible block size in Firefox cache files.
  _MINUMUM_BLOCK_SIZE = 256

  _CACHE_RECORD_HEADER_STRUCT = construct.Struct(
      u'record_header',
      construct.UBInt16(u'major'),
      construct.UBInt16(u'minor'),
      construct.UBInt32(u'location'),
      construct.UBInt32(u'fetch_count'),
      construct.UBInt32(u'last_fetched'),
      construct.UBInt32(u'last_modified'),
      construct.UBInt32(u'expire_time'),
      construct.UBInt32(u'data_size'),
      construct.UBInt32(u'request_size'),
      construct.UBInt32(u'info_size'))

  _CACHE_RECORD_HEADER_SIZE = _CACHE_RECORD_HEADER_STRUCT.sizeof()

  # TODO: change into regexp.
  _CACHE_FILENAME = (
      pyparsing.Word(pyparsing.hexnums, exact=5) +
      pyparsing.Word(u'm', exact=1) +
      pyparsing.Word(pyparsing.nums, exact=2))

  FIREFOX_CACHE_CONFIG = collections.namedtuple(
      u'firefox_cache_config',
      u'block_size first_record_offset')

  def _GetFirefoxConfig(self, file_object, display_name):
    """Determine cache file block size.

    Args:
      file_object: A file-like object.
      display_name: the display name.

    Raises:
      UnableToParseFile: if no valid cache record could be found.
    """
    # There ought to be a valid record within the first 4 MiB. We use this
    # limit to prevent reading large invalid files.
    to_read = min(file_object.get_size(), self._INITIAL_CACHE_FILE_SIZE)

    while file_object.get_offset() < to_read:
      offset = file_object.get_offset()

      try:
        # We have not yet determined the block size, so we use the smallest
        # possible size.
        fetched, _, _ = self._NextRecord(
            file_object, display_name, self._MINUMUM_BLOCK_SIZE)

        record_size = (
            self._CACHE_RECORD_HEADER_SIZE + fetched.request_size +
            fetched.info_size)

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
        logging.debug(u'[{0:s}] {1:s}:{2:d}: Invalid record.'.format(
            self.NAME, display_name, offset))

    raise errors.UnableToParseFile(
        u'Could not find a valid cache record. Not a Firefox cache file.')

  def _NextRecord(self, file_object, display_name, block_size):
    """Provide the next cache record.

    Args:
      file_object: A file-like object.
      display_name: the display name.
      block_size: the block size.

    Returns:
      A tuple containing the fetched, modified and expire event objects
      (instances of EventObject) or None.
    """
    offset = file_object.get_offset()

    try:
      cache_record_header = self._CACHE_RECORD_HEADER_STRUCT.parse_stream(
          file_object)
    except (IOError, construct.FieldError):
      raise IOError(u'Unable to parse stream.')

    if not self._ValidateCacheRecordHeader(cache_record_header):
      # Move reader to next candidate block.
      file_offset = block_size - self._CACHE_RECORD_HEADER_SIZE
      file_object.seek(file_offset, os.SEEK_CUR)
      raise IOError(u'Not a valid Firefox cache record.')

    # The last byte in a request is null.
    url = file_object.read(cache_record_header.request_size)[:-1]

    # HTTP response header, even elements are keys, odd elements values.
    header_data = file_object.read(cache_record_header.info_size)

    request_method, response_code = self._ParseHTTPHeaders(
        header_data, offset, display_name)

    # A request can span multiple blocks, so we use modulo.
    file_offset = file_object.get_offset() - offset
    _, remainder = divmod(file_offset, block_size)

    # Move reader to next candidate block. Include the null-byte skipped above.
    file_object.seek(block_size - remainder, os.SEEK_CUR)

    cache_record_values = {
        u'data_size': cache_record_header.data_size,
        u'fetch_count': cache_record_header.fetch_count,
        u'info_size': cache_record_header.info_size,
        u'location': cache_record_header.location,
        u'major': cache_record_header.major,
        u'minor': cache_record_header.minor,
        u'request_method': request_method,
        u'request_size': cache_record_header.request_size,
        u'response_code': response_code,
        u'version': self.CACHE_VERSION,
        u'url': url}

    fetched = FirefoxCacheEvent(
        cache_record_header.last_fetched,
        eventdata.EventTimestamp.LAST_VISITED_TIME, cache_record_values)

    if cache_record_header.last_modified:
      modified = FirefoxCacheEvent(
          cache_record_header.last_modified,
          eventdata.EventTimestamp.WRITTEN_TIME, cache_record_values)
    else:
      modified = None

    if cache_record_header.expire_time:
      expire = FirefoxCacheEvent(
          cache_record_header.expire_time,
          eventdata.EventTimestamp.EXPIRATION_TIME, cache_record_values)
    else:
      expire = None

    return fetched, modified, expire

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Firefox cache file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    display_name = parser_mediator.GetDisplayName()

    try:
      # Match cache filename. Five hex characters + 'm' + two digit
      # number, e.g. '01ABCm02'. 'm' is for metadata. Cache files with 'd'
      # instead contain data only.
      self._CACHE_FILENAME.parseString(file_entry.name)
    except pyparsing.ParseException:
      if not file_entry.name.startswith(u'_CACHE_00'):
        raise errors.UnableToParseFile(u'Not a Firefox cache1 file.')

    firefox_config = self._GetFirefoxConfig(file_object, display_name)

    file_object.seek(firefox_config.first_record_offset)

    while file_object.get_offset() < file_object.get_size():
      try:
        fetched, modified, expire = self._NextRecord(
            file_object, display_name, firefox_config.block_size)
        parser_mediator.ProduceEvent(fetched)

        if modified:
          parser_mediator.ProduceEvent(modified)

        if expire:
          parser_mediator.ProduceEvent(expire)
      except IOError:
        file_offset = file_object.get_offset() - self._MINUMUM_BLOCK_SIZE
        logging.debug((
            u'[{0:s}] Invalid cache record in file: {1:s} at offset: '
            u'{2:d}.').format(self.NAME, display_name, file_offset))


manager.ParsersManager.RegisterParsers([
    FirefoxCacheParser, FirefoxOldCacheParser])
