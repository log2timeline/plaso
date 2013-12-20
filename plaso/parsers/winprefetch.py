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


class WinPrefetchEventContainer(event.EventContainer):
  """Convenience class for a Windows Prefetch event container."""

  def __init__(self, file_header, file_information, volume_information,
               volume_path):
    """Initializes the event container.

    Args:
      file_header: The file header structure.
      file_information: The file information structure.
      volume_information: The volume information structure.
      volume_path: The volume path string.
    """
    super(WinPrefetchEventContainer, self).__init__()

    self.data_type = 'windows:prefetch'

    self.offset = 0

    self.version = file_header.get('version', None)
    self.executable = binary.Ut16StreamCopyToString(
        file_header.get('executable', ''))
    self.prefetch_hash = file_header.get('prefetch_hash', None)

    self.run_count = file_information.get('run_count', None)

    if volume_information:
      self.volume_serial = volume_information.get('volume_serial', None)

    self.volume_path = volume_path


class WinPrefetchParser(parser.BaseParser):
  """A parser for Windows Prefetch files."""

  NAME = 'prefetch'

  FILE_SIGNATURE = 'SCCA'

  FILE_HEADER_STRUCT = construct.Struct(
      'file_header',
      construct.ULInt32('version'),
      construct.String('signature', 4),
      construct.Padding(4),
      construct.ULInt32('file_size'),
      construct.String('executable', 60),
      construct.ULInt32('prefetch_hash'),
      construct.ULInt32('flags'))

  FILE_INFORMATION_V17 = construct.Struct(
      'file_information_v17',
      construct.Padding(16),
      construct.ULInt32('dll_offset'),
      construct.ULInt32('dll_size'),
      construct.ULInt32('volume_information_offset'),
      construct.Padding(8),
      construct.ULInt64('last_run_time'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(4))

  FILE_INFORMATION_V23 = construct.Struct(
      'file_information_v23',
      construct.Padding(16),
      construct.ULInt32('dll_offset'),
      construct.ULInt32('dll_size'),
      construct.ULInt32('volume_information_offset'),
      construct.Padding(16),
      construct.ULInt64('last_run_time'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(84))

  FILE_INFORMATION_V26 = construct.Struct(
      'file_information_v26',
      construct.Padding(16),
      construct.ULInt32('dll_offset'),
      construct.ULInt32('dll_size'),
      construct.ULInt32('volume_information_offset'),
      construct.Padding(16),
      construct.ULInt64('last_run_time'),
      construct.ULInt64('last_run_time1'),
      construct.ULInt64('last_run_time2'),
      construct.ULInt64('last_run_time3'),
      construct.ULInt64('last_run_time4'),
      construct.ULInt64('last_run_time5'),
      construct.ULInt64('last_run_time6'),
      construct.ULInt64('last_run_time7'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(96))

  # Note that at the moment for the purpose of this parser
  # the v23 and v26 volume information structures are the same as v17.
  VOLUME_INFORMATION_V17 = construct.Struct(
      'volume_information_v17',
      construct.ULInt32('name_offset'),
      construct.ULInt32('name_number_of_characters'),
      construct.ULInt64('creation_time'),
      construct.ULInt32('volume_serial'),
      construct.Padding(8),
      construct.ULInt32('directory_strings_offset'),
      construct.Padding(4))

  def _ParseFileHeader(self, file_object):
    """Parses the file header.

    Args:
      file_object: A file-like object to read data from.

    Returns:
      The file header construct object.
    """
    try:
      file_header = self.FILE_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse file header. '
          u'Reason given: {}'.format(exception))

    if not file_header:
      raise errors.UnableToParseFile('Unable to read file header')

    if file_header.get('signature', None) != self.FILE_SIGNATURE:
      raise errors.UnableToParseFile('Unsupported file signature')

    return file_header

  def _ParseFileInformation(self, file_object, format_version):
    """Parses the file information.

    Args:
      file_object: A file-like object to read data from.
      format_version: The format version.

    Returns:
      The file information construct object.
    """
    try:
      if format_version == 17:
        file_information = self.FILE_INFORMATION_V17.parse_stream(file_object)
      elif format_version == 23:
        file_information = self.FILE_INFORMATION_V23.parse_stream(file_object)
      elif format_version == 26:
        file_information = self.FILE_INFORMATION_V26.parse_stream(file_object)
      else:
        file_information = None
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse file information v{0:d}. '
          u'Reason given: {1}'.format(format_version, exception))

    if not file_information:
      raise errors.UnableToParseFile('Unable to read file information')
    return file_information

  def _ParseVolumeInformation(self, file_object, volume_information_offset):
    """Parses the volume information.

    Args:
      file_object: A file-like object to read data from.
      volume_information_offset: The offset relative from start of the file
                                 to the volume information.

    Returns:
      The volume information construct object or None if not available.
    """
    if volume_information_offset > 0:
      file_object.seek(volume_information_offset, os.SEEK_SET)

      try:
        volume_information = self.VOLUME_INFORMATION_V17.parse_stream(
            file_object)
      except (IOError, construct.FieldError) as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse volume information v17. '
            u'Reason given: {}'.format(exception))
    else:
      volume_information = None
    return volume_information

  def _ParseVolumePath(self, file_object, volume_path_offset, volume_path_size):
    """Parses the volume path.

    This function expects the current offset of the file-like object to point
    as the end of the volume information structure.

    Args:
      file_object: A file-like object to read data from.
      volume_path_offset: The offset relative from start of the volume
                          information to the volume path.
      volume_path_size: The byte size of the volume path data.

    Returns:
      A Unicode string containing the volume path or None if not available.
    """
    if volume_path_offset >= 36 and volume_path_size > 0:
      # Correct for the part of volume information structure we've already read.
      volume_path_offset -= 36
      file_object.seek(volume_path_offset, os.SEEK_CUR)

      volume_path = binary.ReadUtf16Stream(
          file_object, byte_size=volume_path_size)
    else:
      volume_path = None

    return volume_path

  def Parse(self, file_object):
    """Extract data from a Windows Prefetch file.

    Args:
      file_object: A file-like object to read data from.

    Yields:
      An event container (EventContainer) that contains the parsed attributes.
    """
    file_header = self._ParseFileHeader(file_object)

    format_version = file_header.get('version', None)
    if format_version not in [17, 23, 26]:
      raise errors.UnableToParseFile(
          'Unsupported format version: %d' % format_version)

    file_information = self._ParseFileInformation(file_object, format_version)

    volume_information_offset = file_information.get(
        'volume_information_offset', 0)

    volume_information = self._ParseVolumeInformation(
        file_object, volume_information_offset)

    if volume_information:
      volume_path_offset = volume_information.get('name_offset', 0)
      volume_path_size = 2 * volume_information.get(
          'name_number_of_characters', 0)
    else:
      volume_path_offset = 0
      volume_path_size = 0

    volume_path = self._ParseVolumePath(
        file_object, volume_path_offset, volume_path_size)

    container = WinPrefetchEventContainer(
        file_header, file_information, volume_information, volume_path)

    dll_offset = file_information.get('dll_offset', 0)
    dll_size = file_information.get('dll_size', 0)

    if dll_offset > 0 and dll_size > 0:
      file_object.seek(dll_offset, os.SEEK_SET)
      dll_data = file_object.read(dll_size)
      mapped_files = binary.ArrayOfUt16StreamCopyToString(dll_data)

      if volume_path:
        executable = binary.Ut16StreamCopyToString(
            file_header.get('executable', ''))

        for dll_name in mapped_files:
          if dll_name.endswith(executable):
            _, _, path = dll_name.partition(volume_path)
            container.path = path
    else:
      mapped_files = []

    container.mapped_files = mapped_files

    timestamp = file_information.get('last_run_time', 0)
    container.Append(event.FiletimeEvent(
        timestamp, eventdata.EventTimestamp.LAST_RUNTIME,
        container.data_type))

    # Check for the 7 older last run time values available in v26.
    if format_version == 26:
      for last_run_time_index in range(1, 8):
        last_run_time_identifier = 'last_run_time{0:d}'.format(
            last_run_time_index)

        timestamp = file_information.get(last_run_time_identifier, 0)
        if timestamp:
          container.Append(event.FiletimeEvent(
              timestamp,
              u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME),
              container.data_type))

    if volume_information:
      timestamp = volume_information.get('creation_time', 0)

      if timestamp:
        container.Append(event.FiletimeEvent(
            timestamp, eventdata.EventTimestamp.CREATION_TIME,
            container.data_type))

    yield container
