#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implements a parser for Firefox cache files."""

import collections
import logging
import os

import construct
import pyparsing

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface


__author__ = 'Petter Bjelland (petter.bjelland@gmail.com)'


class FirefoxCacheEvent(time_events.PosixTimeEvent):
  """Convenience class for a Firefox cache record event."""

  DATA_TYPE = 'firefox:cache:record'

  def __init__(self, metadata, request_method, url, response_code):
    super(FirefoxCacheEvent, self).__init__(
        metadata.last_fetched, eventdata.EventTimestamp.ADDED_TIME)

    self.last_modified = metadata.last_modified
    self.major = metadata.major
    self.minor = metadata.minor
    self.location = metadata.location
    self.last_fetched = metadata.last_fetched
    self.expire_time = metadata.expire_time
    self.fetch_count = metadata.fetch_count
    self.request_size = metadata.request_size
    self.info_size = metadata.info_size
    self.data_size = metadata.data_size
    self.request_method = request_method
    self.url = url
    self.response_code = response_code


class FirefoxCacheParser(interface.BaseParser):
  """Extract cached records from Firefox."""

  NAME = 'firefox_cache'

  # Number of bytes allocated to a cache record metadata.
  RECORD_HEADER_SIZE = 36

  # Initial size of Firefox >= 4 cache files.
  INITIAL_CACHE_FILE_SIZE = 1024 * 1024 * 4

  # Smallest possible block size in Firefox cache files.
  MIN_BLOCK_SIZE = 256

  RECORD_HEADER_STRUCT = construct.Struct(
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

  ALTERNATIVE_CACHE_NAME = (pyparsing.Word(pyparsing.hexnums, exact=5) +
      pyparsing.Word('m', exact=1) + pyparsing.Word(pyparsing.nums, exact=2))

  FIREFOX_CACHE_CONFIG = collections.namedtuple(
      u'firefox_cache_config',
      u'block_size first_record_offset')

  REQUEST_METHODS = [
      u'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
      u'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']

  def _GetFirefoxConfig(self, file_entry):
    """Determine cache file block size. Raises exception if not found."""

    if file_entry.name[0:9] != '_CACHE_00':
      try:
        # Match alternative filename. Five hex characters + 'm' + two digit
        # number, e.g. '01ABCm02'. 'm' is for metadata. Cache files with 'd'
        # instead contain data only.
        self.ALTERNATIVE_CACHE_NAME.parseString(file_entry.name)
      except pyparsing.ParseException:
        raise errors.UnableToParseFile(u'Not a Firefox cache file.')

    file_object = file_entry.GetFileObject()

    # There ought to be a valid record within the first 4MB. We use this
    # limit to prevent reading large invalid files.
    to_read = min(file_object.get_size(), self.INITIAL_CACHE_FILE_SIZE)

    while file_object.get_offset() < to_read:
      offset = file_object.get_offset()

      try:
        # We have not yet determined the block size, so we use the smallest
        # possible size.
        record = self.__NextRecord(file_entry.name, file_object,
            self.MIN_BLOCK_SIZE)

        record_size = (
            self.RECORD_HEADER_SIZE + record.request_size + record.info_size)

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

  def __Accept(self, candidate, block_size):
    """Determine whether the candidate is a valid cache record."""

    record_size = (self.RECORD_HEADER_SIZE + candidate.request_size
        + candidate.info_size)

    return (candidate.request_size > 0 and candidate.fetch_count > 0
        and candidate.major == 1 and record_size // block_size < 256)

  def __NextRecord(self, filename, file_object, block_size):
    """Provide the next cache record."""

    offset = file_object.get_offset()

    try:
      candidate = self.RECORD_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError):
      raise IOError(u'Unable to parse stream.')

    if not self.__Accept(candidate, block_size):
      # Move reader to next candidate block.
      file_object.seek(block_size - self.RECORD_HEADER_SIZE, os.SEEK_CUR)
      raise IOError(u'Not a valid Firefox cache record.')

    # The last byte in a request is null.
    url = file_object.read(candidate.request_size)[:-1]

    # HTTP response header, even elements are keys, odd elements values.
    headers = file_object.read(candidate.info_size)

    request_method, _, _ = (
        headers.partition('request-method\x00')[2].partition('\x00'))

    _, _, response_head = headers.partition('response-head\x00')

    response_code, _, _ = response_head.partition('\r\n')

    if request_method not in self.REQUEST_METHODS:
      safe_headers = headers.decode('ascii', errors='replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Unknown HTTP method \'{3:s}\'. Response '
          u'headers: \'{4:s}\'').format(
              self.NAME, filename, offset, request_method, safe_headers))

    if response_code[0:4] != 'HTTP':
      safe_headers = headers.decode('ascii', errors='replace')
      logging.debug((
          u'[{0:s}] {1:s}:{2:d}: Could not determine HTTP response code. '
          u'Response headers: \'{3:s}\'.').format(
              self.NAME, filename, offset, safe_headers))

    # A request can span multiple blocks, so we use modulo.
    _, remainder = divmod(file_object.get_offset() - offset, block_size)

    # Move reader to next candidate block. Include the null-byte skipped above.
    file_object.seek(block_size - remainder, os.SEEK_CUR)

    return FirefoxCacheEvent(candidate, request_method, url, response_code)

  def Parse(self, parser_context, file_entry):
    """Extract records from a Firefox cache file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    firefox_config = self._GetFirefoxConfig(file_entry)

    file_object = file_entry.GetFileObject()

    file_object.seek(firefox_config.first_record_offset)

    while file_object.get_offset() < file_object.get_size():
      try:
        event_object = self.__NextRecord(
            file_entry.name, file_object, firefox_config.block_size)

        parser_context.ProduceEvent(
            event_object, parser_name=self.NAME, file_entry=file_entry)

      except IOError:
        logging.debug(u'[{0:s}] {1:s}:{2:d}: Invalid cache record.'.format(
            self.NAME, file_entry.name,
            file_object.get_offset() - self.MIN_BLOCK_SIZE))

    file_object.close()
