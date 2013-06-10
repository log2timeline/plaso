#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Parser for Windows Prefetch files."""
import os
import construct

from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class WinPrefetchEventContainer(event.EventContainer):
  """Convenience class for a Windows Prefetch event container."""

  def __init__(self, magic_header, header, executable, run, volume, vol_path):
    """Initializes the event container."""
    super(WinPrefetchEventContainer, self).__init__()

    self.data_type = 'windows:prefetch:prefetch'

    self.offset = 0

    self.executable = executable
    self.hash_value = '0x{:08X}'.format(header.get('hash_value', 0))
    self.version = magic_header.get('version', 0x11)
    self.run_count = run.get('run_count', 0)
    self.volume_serial = '0x{:08X}'.format(volume.get('volume_serial', 0))
    self.volume_path = vol_path


class WinPrefetchParser(parser.PlasoParser):
  """Parses Windows Prefetch and Superfetch files."""

  # Define a list of all structs used.
  FILE_HEADER_STRUCT = construct.Struct(
      'header_signature', construct.ULInt16('version'), construct.Padding(2),
      construct.String('magic', 4), construct.Padding(4),
      construct.ULInt32('end_of_file'))

  HEADER_STRUCT = construct.Struct(
      'header', construct.ULInt32('hash_value'), construct.Padding(4),
      construct.ULInt32('header_size'), construct.Padding(12),
      construct.ULInt32('dll_ofs'), construct.ULInt32('dll_length'),
      construct.ULInt32('vol_start'))

  VOLUME_STRUCT = construct.Struct(
      'volume', construct.ULInt32('path_bytes'),
      construct.ULInt32('path_length'), construct.ULInt64('created'),
      construct.ULInt32('volume_serial'), construct.ULInt32('dir_bytes'),
      construct.ULInt32('dir_numbers'))

  def Parse(self, file_object):
    """Extract data from a Windows Prefetch file.

    Args:
      file_object: a file-like object to read data from.

    Returns:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    try:
      magic_header = self.FILE_HEADER_STRUCT.parse_stream(file_object)
    except construct.FieldError as e:
      raise errors.UnableToParseFile(
          u'Not a prefetch file, unable to parse. Reason given: {}'.format(e))
    except IOError as e:
      raise errors.UnableToParseFile(
          u'Not a prefetch file, unable to parse. Reason given: {}'.format(e))

    if not magic_header:
      raise errors.UnableToParseFile('Unable to read in data')

    magic = magic_header.get('magic', None)
    if magic != 'SCCA':
      raise errors.UnableToParseFile('Wrong Magic Value')

    executable = binary.ReadUtf16Stream(file_object)

    # TODO: Change this fixed location for a more elegant solution or change
    # the header struct to properly seek to this location.
    # Seek to the beginning of the header struct.
    file_object.seek(0x4c - file_object.tell(), os.SEEK_CUR)
    header = self.HEADER_STRUCT.parse_stream(file_object)

    if magic_header.get('version', 0x11) is 0x11:
      last_run_ofs = 0x78
      run_count_ofs = 0x90
    else:
      last_run_ofs = 0x80
      run_count_ofs = 0x98

    file_object.seek(last_run_ofs - file_object.tell(), os.SEEK_CUR)
    run_struct = construct.Struct(
        'run', construct.ULInt64('last_run'), construct.Padding(
            run_count_ofs - last_run_ofs - 8), construct.ULInt32('run_count'))

    run = run_struct.parse_stream(file_object)

    file_object.seek(
        header.get('vol_start', 0) - file_object.tell(), os.SEEK_CUR)
    volume = self.VOLUME_STRUCT.parse_stream(file_object)

    file_object.seek(
        header.get('vol_start', 0) + volume.get('path_bytes', 0) -
        file_object.tell(), os.SEEK_CUR)
    volume_path = binary.ReadUtf16Stream(
        file_object, byte_size=(volume.get('path_length', 0) * 2 + 2))

    file_object.seek(
        header.get('dll_ofs', 0) - file_object.tell(), os.SEEK_CUR)

    container = WinPrefetchEventContainer(
        magic_header, header, executable, run, volume, volume_path)

    mapped_files = []
    dll_read = 0
    while dll_read < header.get('dll_length', 0):
      dll_name = binary.ReadUtf16Stream(file_object)

      # UTF-16 so multiply by 2, and then add 4 for end of line for each line.
      dll_read += len(dll_name) * 2 + 4
      mapped_files.append(dll_name)

      if dll_name.endswith(executable):
        path, _, name = dll_name.partition(volume_path)
        container.path = name

    container.mapped_files = mapped_files

    container.Append(event.FiletimeEvent(
        run.get('last_run', 0),
        eventdata.EventTimestamp.CREATION_TIME,
        container.data_type))

    container.Append(event.FiletimeEvent(
        volume.get('created', 0),
        eventdata.EventTimestamp.LAST_RUNTIME,
        container.data_type))

    return container

