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

  DATA_TYPE = 'firefox:cache:record'

  def __init__(
      self, timestamp_type, timestamp, version, metadata, request_method, url,
      response_code):
    super(FirefoxCacheEvent, self).__init__(timestamp, timestamp_type)

    self.cache_version = version

    # Fields found in both cache 1 and 2.
    self.last_modified = metadata.last_modified
    self.fetch_count = metadata.fetch_count
    self.request_size = metadata.request_size
    self.request_method = request_method
    self.url = url
    self.response_code = response_code

    if not version == 1:
      return

    # Fields found in cache 1 only.
    self.major = metadata.major
    self.minor = metadata.minor
    self.location = metadata.location
    self.info_size = metadata.info_size
    self.data_size = metadata.data_size


class FirefoxCacheParser(interface.BaseParser):
  """Extract cache version 2 records from Firefox >= 32."""

  NAME = u'firefox_cache'

  DESCRIPTION = u'Parser for Firefox Cache files.'

  CACHE_VERSION = 2

  REQUEST_METHODS = frozenset([
      u'CONNECT', u'DELETE', u'GET', u'HEAD', u'OPTIONS',
      u'PATCH', u'POST', u'PUT', u'TRACE'])

  MAX_URL_LENGTH = 65536

  # Cache 2 filenames are SHA-1 hex digests.
  CACHE_NAME = pyparsing.Word(pyparsing.hexnums, exact=40)

  # The last four bytes of a file gives the size of the cached content.
  LENGTH = construct.Struct(u'length', construct.UBInt32(u'length'))

  CHUNK_SIZE = 512 * 1024

  CACHE_RECORD_HEADER_STRUCT = construct.Struct(
      u'record_header',
      construct.UBInt32(u'major'),
      construct.UBInt32(u'fetch_count'),
      construct.UBInt32(u'last_fetched'),
      construct.UBInt32(u'last_modified'),
      construct.UBInt32(u'frecency'),
      construct.UBInt32(u'expire_time'),
      construct.UBInt32(u'request_size'))

  def _Accept(self, candidate):
    """Determine whether the candidate is a valid cache record."""

    return (
        candidate.request_size > 0
        and candidate.request_size < self.MAX_URL_LENGTH
        and candidate.major == 1 and candidate.last_fetched > 0
        and candidate.fetch_count > 0)

  def _ParseHTTPHeaders(self, filename, offset, headers):
    """Extract relevant information from HTTP header."""

    try:
      http_header_start = headers.index(u'request-method')
    except ValueError:
      logging.debug(u'No request method in header: "{0:s}"'.format(headers))
      return None, None

    # HTTP request and response headers.
    http_headers = headers[http_header_start::]

    header_parts = http_headers.split(u'\x00')

    request_method = header_parts[1]

    if request_method not in self.REQUEST_METHODS:
      safe_headers = headers.decode('ascii', errors='replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Unknown HTTP method \'{3:s}\'. Response '
          u'headers: \'{4:s}\'').format(
              self.NAME, filename, offset, request_method, safe_headers))

    try:
      response_head_start = http_headers.index(u'response-head')
    except ValueError:
      logging.debug(u'No response head in header: "{0:s}"'.format(headers))
      return request_method, None

    # HTTP response headers.
    response_head = http_headers[response_head_start::]

    response_head_parts = response_head.split(u'\x00')

    # Response code, followed by other response header key-value pairs,
    # separated by newline.
    response_head_text = response_head_parts[1]
    response_head_text_parts = response_head_text.split(u'\r\n')

    # The first line contains response code.
    response_code = response_head_text_parts[0]

    if not response_code.startswith(u'HTTP'):
      safe_headers = headers.decode('ascii', errors='replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Could not determine HTTP response code. '
          u'Response headers: \'{3:s}\'.').format(
              self.NAME, filename, offset, safe_headers))

    return request_method, response_code

  def _GetStartOfMetadata(self, file_object):
    """Determine the byte offset of the cache record metadata in cache file.

       This method is inspired by the unlicensed work of EnCase instructor
       James Habben: https://github.com/JamesHabben/FirefoxCache2

    Args:
      file_object: The file containing the cache record.
    """

    file_object.seek(-4, os.SEEK_END)

    try:
      length = self.LENGTH.parse_stream(file_object).length
    except (IOError, construct.FieldError):
      raise IOError(u'Could not find metadata offset in Firefox cache file.')

    # Firefox splits the content into chunks.
    hash_chunks = length // self.CHUNK_SIZE
    if length % self.CHUNK_SIZE != 0:
      hash_chunks += 1

    # Each chunk in the cached record is padded with two bytes.
    total_chunk_padding = hash_chunks * 2

    return length + total_chunk_padding

  def Parse(self, parser_mediator, **kwargs):
    """Extract records from a Firefox cache file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """

    file_entry = parser_mediator.GetFileEntry()

    try:
      # Match cache2 filename (SHA-1 hex of cache record key).
      self.CACHE_NAME.parseString(file_entry.name)
    except pyparsing.ParseException:
      raise errors.UnableToParseFile(u'Not a Firefox cache2 file.')

    if file_entry.GetStat().size == 0:
      raise errors.UnableToParseFile(u'Empty file.')

    file_object = parser_mediator.GetFileObject()

    meta_start = self._GetStartOfMetadata(file_object)

    file_object.seek(meta_start, os.SEEK_SET)

    # The first four bytes of metadata is a hash value of the cached content.
    file_object.read(4)

    try:
      candidate = self.CACHE_RECORD_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError):
      file_object.close()
      raise errors.UnableToParseFile(u'Not a Firefox cache2 file.')

    if not self._Accept(candidate):
      file_object.close()
      raise errors.UnableToParseFile(u'Not a valid Firefox cache2 record.')

    url = file_object.read(candidate.request_size)

    headers = file_object.read()

    request_method, response_code = self._ParseHTTPHeaders(
        file_entry.name, meta_start, headers)

    args = [self.CACHE_VERSION, candidate, request_method, url, response_code]

    parser_mediator.ProduceEvent(FirefoxCacheEvent(
        eventdata.EventTimestamp.LAST_VISITED_TIME,
        candidate.last_fetched, *args))

    if candidate.last_modified:
      parser_mediator.ProduceEvent(FirefoxCacheEvent(
          eventdata.EventTimestamp.WRITTEN_TIME, candidate.last_modified,
          *args))

    if candidate.expire_time:
      parser_mediator.ProduceEvent(FirefoxCacheEvent(
          eventdata.EventTimestamp.EXPIRATION_TIME, candidate.expire_time,
          *args))

    file_object.close()


class FirefoxOldCacheParser(FirefoxCacheParser):
  """Extract cached records from Firefox < 32."""

  NAME = 'firefox_old_cache'

  CACHE_VERSION = 1

  # Number of bytes allocated to a cache record metadata.
  RECORD_HEADER_SIZE = 36

  # Initial size of Firefox >= 4 cache files.
  INITIAL_CACHE_FILE_SIZE = 1024 * 1024 * 4

  # Smallest possible block size in Firefox cache files.
  MIN_BLOCK_SIZE = 256

  OLD_CACHE_RECORD_HEADER_STRUCT = construct.Struct(
      'record_header',
      construct.UBInt16('major'),
      construct.UBInt16('minor'),
      construct.UBInt32('location'),
      construct.UBInt32('fetch_count'),
      construct.UBInt32('last_fetched'),
      construct.UBInt32('last_modified'),
      construct.UBInt32('expire_time'),
      construct.UBInt32('data_size'),
      construct.UBInt32('request_size'),
      construct.UBInt32('info_size'))

  ALTERNATIVE_CACHE_NAME = (
      pyparsing.Word(pyparsing.hexnums, exact=5) + pyparsing.Word('m', exact=1)
      + pyparsing.Word(pyparsing.nums, exact=2))

  FIREFOX_CACHE_CONFIG = collections.namedtuple(
      u'firefox_cache_config',
      u'block_size first_record_offset')

  def _GetFirefoxConfig(self, file_entry):
    """Determine cache file block size. Raises exception if not found."""

    file_object = file_entry.GetFileObject()

    # There ought to be a valid record within the first 4MB. We use this
    # limit to prevent reading large invalid files.
    to_read = min(file_object.get_size(), self.INITIAL_CACHE_FILE_SIZE)

    while file_object.get_offset() < to_read:
      offset = file_object.get_offset()

      try:
        # We have not yet determined the block size, so we use the smallest
        # possible size.
        fetched, _, _ = self._NextRecord(
            file_entry.name, file_object, self.MIN_BLOCK_SIZE)

        record_size = (
            self.RECORD_HEADER_SIZE + fetched.request_size + fetched.info_size)

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
            self.NAME, file_entry.name, offset))

    raise errors.UnableToParseFile(
        u'Could not find a valid cache record. '
        u'Not a Firefox cache file.')

  def _NextRecord(self, filename, file_object, block_size):
    """Provide the next cache record."""

    offset = file_object.get_offset()

    try:
      candidate = self.OLD_CACHE_RECORD_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError):
      raise IOError(u'Unable to parse stream.')

    if not self._Accept(candidate):
      # Move reader to next candidate block.
      file_object.seek(block_size - self.RECORD_HEADER_SIZE, os.SEEK_CUR)
      raise IOError(u'Not a valid Firefox cache record.')

    # The last byte in a request is null.
    url = file_object.read(candidate.request_size)[:-1]

    # HTTP response header, even elements are keys, odd elements values.
    headers = file_object.read(candidate.info_size)

    request_method, response_code = self._ParseHTTPHeaders(
        filename, offset, headers)

    # A request can span multiple blocks, so we use modulo.
    _, remainder = divmod(file_object.get_offset() - offset, block_size)

    # Move reader to next candidate block. Include the null-byte skipped above.
    file_object.seek(block_size - remainder, os.SEEK_CUR)

    args = [self.CACHE_VERSION, candidate, request_method, url, response_code]

    fetched = FirefoxCacheEvent(
        eventdata.EventTimestamp.LAST_VISITED_TIME,
        candidate.last_fetched, *args)

    modified = None
    expire = None

    if candidate.last_modified:
      modified = FirefoxCacheEvent(
          eventdata.EventTimestamp.WRITTEN_TIME, candidate.last_modified, *args)

    if candidate.expire_time:
      expire = FirefoxCacheEvent(
          eventdata.EventTimestamp.EXPIRATION_TIME, candidate.expire_time,
          *args)

    return fetched, modified, expire

  def Parse(self, parser_mediator, **kwargs):
    """Extract records from a Firefox cache file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    file_entry = parser_mediator.GetFileEntry()

    try:
      # Match alternative filename. Five hex characters + 'm' + two digit
      # number, e.g. '01ABCm02'. 'm' is for metadata. Cache files with 'd'
      # instead contain data only.
      self.ALTERNATIVE_CACHE_NAME.parseString(file_entry.name)
    except pyparsing.ParseException:
      if not file_entry.name.startswith('_CACHE_00'):
        file_object.close()
        raise errors.UnableToParseFile(u'Not a Firefox cache1 file.')

    firefox_config = self._GetFirefoxConfig(file_entry)

    file_object.seek(firefox_config.first_record_offset)

    while file_object.get_offset() < file_object.get_size():
      try:
        fetched, modified, expire = self._NextRecord(
            file_entry.name, file_object, firefox_config.block_size)
        parser_mediator.ProduceEvent(fetched)

        if modified:
          parser_mediator.ProduceEvent(modified)

        if expire:
          parser_mediator.ProduceEvent(expire)
      except IOError:
        logging.debug(u'[{0:s}] {1:s}:{2:d}: Invalid cache record.'.format(
            self.NAME, file_entry.name,
            file_object.get_offset() - self.MIN_BLOCK_SIZE))

    file_object.close()


manager.ParsersManager.RegisterParsers(
    [FirefoxCacheParser, FirefoxOldCacheParser])
