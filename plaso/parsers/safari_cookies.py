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
"""Parser for Safari Binary Cookie files."""

import construct
import logging

from plaso.events import time_events

from plaso.lib import errors
from plaso.lib import eventdata

# Need to register cookie plugins.
from plaso.parsers import cookie_plugins    # pylint: disable=unused-import
from plaso.parsers import interface
from plaso.parsers import manager

from plaso.parsers.cookie_plugins import interface as cookie_interface


class BinaryCookieEvent(time_events.CocoaTimeEvent):
  """A convenience class for a binary cookie event."""

  DATA_TYPE = 'safari:cookie:entry'

  def __init__(self, timestamp, timestamp_desc, flags, url, value, name, path):
    """Initialize the binary cookie.

    Args:
      timestamp: The timestamp in Cocoa format.
      timestamp_desc: The usage string, describing the timdestamp value.
      flags: String containing the flags for the cookie.
      url: The URL where this cookie is valid.
      value: The value or data of the cookie.
      name: The name of the cookie.
      path: The path of the cookie.
    """
    super(BinaryCookieEvent, self).__init__(timestamp, timestamp_desc)
    self.cookie_name = name
    self.cookie_value = value
    self.flags = flags
    self.path = path
    self.url = url


class BinaryCookieParser(interface.BaseParser):
  """Parser for Safari Binary Cookie files."""

  NAME = 'binary_cookies'
  DESCRIPTION = u'Parser for Safari Binary Cookie files.'

  COOKIE_HEADER = construct.Struct(
      'binary_cookie_header',
      construct.UBInt32('pages'),
      construct.Array(lambda ctx: ctx.pages, construct.UBInt32('page_sizes')))

  COOKIE_DATA = construct.Struct(
      'binary_cookie_data',
      construct.ULInt32('size'),
      construct.Bytes('unknown_1', 4),
      construct.ULInt32('flags'),
      construct.Bytes('unknown_2', 4),
      construct.ULInt32('url_offset'),
      construct.ULInt32('name_offset'),
      construct.ULInt32('path_offset'),
      construct.ULInt32('value_offset'),
      construct.Bytes('end_of_cookie', 8),
      construct.LFloat64('expiration_date'),
      construct.LFloat64('creation_date'))

  PAGE_DATA = construct.Struct(
      'page_data',
      construct.Bytes('header', 4),
      construct.ULInt32('number_of_cookies'),
      construct.Array(
          lambda ctx: ctx.number_of_cookies, construct.ULInt32('offsets')))

  # Cookie flags.
  COOKIE_FLAG_NONE = 0
  COOKIE_FLAG_SECURE = 1
  COOKIE_FLAG_UNKNOWN = 2
  COOKIE_FLAG_HTTP_ONLY = 4

  def __init__(self):
    """Initialize the parser."""
    super(BinaryCookieParser, self).__init__()
    self._cookie_plugins = cookie_interface.GetPlugins()

  def _ParsePage(
      self, page_data, file_entry, parser_context, parser_chain=None):
    """Extract events from a page and produce events.

    Args:
      page_data: Raw bytes of the page.
      file_entry: The file entry (instance of dfvfs.FileEntry).
      parser_context: A parser context object (instance of ParserContext).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    try:
      page = self.PAGE_DATA.parse(page_data)
    except construct.FieldError:
      logging.error(u'Unable to parse page from: {0:s}'.format(
          file_entry.comparable.replace(u'\n', u' - ')))
      return

    for page_offset in page.offsets:
      try:
        cookie = self.COOKIE_DATA.parse(page_data[page_offset:])
      except construct.FieldError:
        logging.error(u'Unable to parse cookie data from offset: {0:d}'.format(
            page_offset))
        continue

      # The offset is determine by the range between the start of the current
      # offset until the start of the next offset. Thus we need to determine
      # the proper ordering of the offsets, since they are not always in the
      # same ordering.
      offset_dict = {
          cookie.url_offset: u'url', cookie.name_offset: u'name',
          cookie.value_offset: u'value', cookie.path_offset: u'path'}

      offsets = sorted(offset_dict.keys())
      offsets.append(cookie.size + page_offset)

      # TODO: Find a better approach to parsing the data than this.
      data_dict = {}
      for current_offset in range(0, len(offsets) - 1):
        # Get the current offset and the offset for the next entry.
        start, end = offsets[current_offset:current_offset+2]
        value = offset_dict.get(offsets[current_offset])
        # Read the data.
        data_all = page_data[start + page_offset:end + page_offset]
        data, _, _ = data_all.partition('\x00')
        data_dict[value] = data

      url = data_dict.get(u'url')
      cookie_name = data_dict.get(u'name')
      cookie_value = data_dict.get(u'value')
      path = data_dict.get(u'path')

      flags = []
      flag_int = cookie.flags
      if flag_int & self.COOKIE_FLAG_HTTP_ONLY:
        flags.append(u'HttpOnly')
      if flag_int & self.COOKIE_FLAG_UNKNOWN:
        flags.append(u'Unknown')
      if flag_int & self.COOKIE_FLAG_SECURE:
        flags.append(u'Secure')

      cookie_flags = u'|'.join(flags)

      if cookie.creation_date:
        event_object = BinaryCookieEvent(
            cookie.creation_date, eventdata.EventTimestamp.CREATION_TIME,
            cookie_flags, url, cookie_value, cookie_name, path)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      if cookie.expiration_date:
        event_object = BinaryCookieEvent(
            cookie.expiration_date, eventdata.EventTimestamp.EXPIRATION_TIME,
            cookie_flags, url, cookie_value, cookie_name, path)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      for cookie_plugin in self._cookie_plugins:
        try:
          cookie_plugin.Process(
              parser_context, cookie_name=data_dict.get(u'name'),
              cookie_data=data_dict.get(u'value'), url=data_dict.get(u'url'),
              parser_chain=parser_chain, file_entry=file_entry)
        except errors.WrongPlugin:
          pass

  def Parse(self, parser_context, file_entry, parser_chain=None):
    """Extract data from a Safari Binary Cookie file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    file_object = file_entry.GetFileObject()

    # Start by verifying magic value.
    # We do this here instead of in the header parsing routine due to the
    # fact that we read an integer there and create an array, which is part
    # of the header. For false hits this could end up with reading large chunks
    # of data, which we don't want for false hits.
    magic = file_object.read(4)
    if magic != 'cook':
      file_object.close()
      raise errors.UnableToParseFile(
          u'The file is not a Binary Cookie file. Unsupported file signature.')

    try:
      header = self.COOKIE_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError):
      file_object.close()
      raise errors.UnableToParseFile(
          u'The file is not a Binary Cookie file (bad header).')

    # Add ourselves to the parser chain, which will be used in all subsequent
    # event creation in this parser.
    parser_chain = self._BuildParserChain(parser_chain)

    for page_size in header.page_sizes:
      page = file_object.read(page_size)
      if len(page) != page_size:
        logging.error(u'Unable to continue parsing Binary Cookie file')
        break

      self._ParsePage(page, file_entry, parser_context, parser_chain)

    file_object.close()


manager.ParsersManager.RegisterParser(BinaryCookieParser)
