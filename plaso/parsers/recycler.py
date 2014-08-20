#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Parser for Windows Recycle files, INFO2 and $I/$R pairs."""

import logging

import construct

from plaso.events import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import utils
from plaso.parsers import interface


class WinRecycleEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Recycle bin EventObject."""

  DATA_TYPE = 'windows:metadata:deleted_item'

  def __init__(
      self, filename_ascii, filename_utf, record_information, record_size):
    """Initializes the event object."""
    timestamp = record_information.get('filetime', 0)

    super(WinRecycleEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.DELETED_TIME)

    if 'index' in record_information:
      self.index = record_information.get('index', 0)
      self.offset = record_size * self.index
    else:
      self.offset = 0

    self.drive_number = record_information.get('drive', None)
    self.file_size = record_information.get('filesize', 0)

    if filename_utf:
      self.orig_filename = filename_utf
    else:
      self.orig_filename = filename_ascii

    # The unicode cast is done on the ASCII string to make
    # comparison work better (sometimes a warning that a comparison
    # could not be made due to the objects being of different type).
    if filename_ascii and unicode(filename_ascii) != filename_utf:
      self.orig_filename_legacy = filename_ascii


class WinRecycleBinParser(interface.BaseParser):
  """Parses the Windows $I recycle files."""

  NAME = 'recycle_bin'

  # Define a list of all structs needed.
  # Struct read from:
  # https://code.google.com/p/rifiuti2/source/browse/trunk/src/rifiuti-vista.h
  RECORD_STRUCT = construct.Struct(
      'record',
      construct.ULInt64('filesize'),
      construct.ULInt64('filetime'))

  MAGIC_STRUCT = construct.ULInt64('magic')

  def Parse(self, parser_context, file_entry):
    """Extract entries from a Windows RecycleBin $Ixx file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object.
    """
    file_object = file_entry.GetFileObject()
    try:
      magic_header = self.MAGIC_STRUCT.parse_stream(file_object)
    except (construct.FieldError, IOError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse $Ixxx file with error: {0:s}'.format(exception))

    if magic_header is not 1:
      raise errors.UnableToParseFile(
          u'Not an $Ixxx file, wrong magic header.')

    # We may have to rely on filenames since this header is very generic.
    # TODO: Rethink this and potentially make a better test.
    base_filename = utils.GetBaseName(file_entry.name)
    if not base_filename.startswith('$I'):
      raise errors.UnableToParseFile(
          u'Not an $Ixxx file, filename doesn\'t start with $I.')

    record = self.RECORD_STRUCT.parse_stream(file_object)
    filename_utf = binary.ReadUtf16Stream(file_object)

    file_object.close()
    yield WinRecycleEvent('', filename_utf, record, 0)


class WinRecycleInfo2Parser(interface.BaseParser):
  """Parses the Windows INFO2 recycle bin file."""

  NAME = 'recycle_bin_info2'

  # Define a list of all structs used.
  INT32_LE = construct.ULInt32('my_int')

  FILE_HEADER_STRUCT = construct.Struct(
      'file_header',
      construct.Padding(8),
      construct.ULInt32('record_size'))

  # Struct based on (-both unicode and legacy string):
  # https://code.google.com/p/rifiuti2/source/browse/trunk/src/rifiuti.h
  RECORD_STRUCT = construct.Struct(
      'record',
      construct.ULInt32('index'),
      construct.ULInt32('drive'),
      construct.ULInt64('filetime'),
      construct.ULInt32('filesize'))

  STRING_STRUCT = construct.CString('legacy_filename')

  # Define a list of needed variables.
  UNICODE_FILENAME_OFFSET = 0x11C
  RECORD_INDEX_OFFSET = 0x108

  def Parse(self, parser_context, file_entry):
    """Extract entries from Windows Recycler INFO2 file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event object.
    """
    file_object = file_entry.GetFileObject()
    try:
      magic_header = self.INT32_LE.parse_stream(file_object)
    except (construct.FieldError, IOError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse INFO2 file with error: {0:s}'.format(exception))

    if magic_header is not 5:
      raise errors.UnableToParseFile(
          u'Not an INFO2 file, wrong magic header.')

    # Since this header value is really generic it is hard not to use filename
    # as an indicator too.
    # TODO: Rethink this and potentially make a better test.
    base_filename = utils.GetBaseName(file_entry.name)
    if not base_filename.startswith('INFO2'):
      raise errors.UnableToParseFile(
          u'Not an INFO2 file, filename isn\'t INFO2.')

    file_header = self.FILE_HEADER_STRUCT.parse_stream(file_object)

    # Limit recrodsize to 65536 to be on the safe side.
    record_size = file_header['record_size']
    if record_size > 65536:
      logging.error((
          u'Record size: {0:d} is too large for INFO2 reducing to: '
          u'65535').format(record_size))
      record_size = 65535

    # If recordsize is 0x320 then we have UTF/unicode names as well.
    read_unicode_names = False
    if record_size is 0x320:
      read_unicode_names = True

    data = file_object.read(record_size)
    while data:
      if len(data) != record_size:
        break
      filename_ascii = self.STRING_STRUCT.parse(data[4:])
      record_information = self.RECORD_STRUCT.parse(
          data[self.RECORD_INDEX_OFFSET:])
      if read_unicode_names:
        filename_utf = binary.ReadUtf16(
            data[self.UNICODE_FILENAME_OFFSET:])
      else:
        filename_utf = u''

      yield WinRecycleEvent(
          filename_ascii, filename_utf, record_information, record_size)

      data = file_object.read(record_size)

    file_object.close()
