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
"""Parser for Windows Prefetch files."""

import os
import construct

from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class WinPrefetchExecutionEventContainer(event.EventContainer):
  """Class that defines a Windows Prefetch execution event."""

  def __init__(self, file_header, file_information, mapped_files):
    """Initializes the event container.

    Args:
      file_header: The file header construct object.
      file_information: The file information construct object.
      mapped_files: The list of mapped filenames.
    """
    super(WinPrefetchExecutionEventContainer, self).__init__()

    self.data_type = 'windows:prefetch:execution'
    self.offset = 0

    self.version = file_header.get('version', None)
    self.executable = binary.Ut16StreamCopyToString(
        file_header.get('executable', ''))
    self.prefetch_hash = file_header.get('prefetch_hash', None)

    self.run_count = file_information.get('run_count', None)
    self.mapped_files = mapped_files

    self.number_of_volumes = file_information.get('number_of_volumes', 0)
    self.volume_serial_numbers = []
    self.volume_device_paths = []

  def AppendVolume(self, volume_serial_number, volume_device_path):
    """Appends a volume.

    Args:
      volume_serial_number: The volume serial number string.
      volume_device_path: The volume device path string.
    """
    self.volume_serial_numbers.append(volume_serial_number)
    self.volume_device_paths.append(volume_device_path)


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
      construct.ULInt32('filenames_offset'),
      construct.ULInt32('filenames_size'),
      construct.ULInt32('volumes_information_offset'),
      construct.ULInt32('number_of_volumes'),
      construct.ULInt32('volumes_information_size'),
      construct.ULInt64('last_run_time'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(4))

  FILE_INFORMATION_V23 = construct.Struct(
      'file_information_v23',
      construct.Padding(16),
      construct.ULInt32('filenames_offset'),
      construct.ULInt32('filenames_size'),
      construct.ULInt32('volumes_information_offset'),
      construct.ULInt32('number_of_volumes'),
      construct.ULInt32('volumes_information_size'),
      construct.Padding(8),
      construct.ULInt64('last_run_time'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(84))

  FILE_INFORMATION_V26 = construct.Struct(
      'file_information_v26',
      construct.Padding(16),
      construct.ULInt32('filenames_offset'),
      construct.ULInt32('filenames_size'),
      construct.ULInt32('volumes_information_offset'),
      construct.ULInt32('number_of_volumes'),
      construct.ULInt32('volumes_information_size'),
      construct.Padding(8),
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

  VOLUME_INFORMATION_V17 = construct.Struct(
      'volume_information_v17',
      construct.ULInt32('device_path_offset'),
      construct.ULInt32('device_path_number_of_characters'),
      construct.ULInt64('creation_time'),
      construct.ULInt32('serial_number'),
      construct.Padding(8),
      construct.ULInt32('directory_strings_offset'),
      construct.Padding(4))

  # Note that at the moment for the purpose of this parser
  # the v23 and v26 volume information structures are the same.
  VOLUME_INFORMATION_V23 = construct.Struct(
      'volume_information_v23',
      construct.ULInt32('device_path_offset'),
      construct.ULInt32('device_path_number_of_characters'),
      construct.ULInt64('creation_time'),
      construct.ULInt32('serial_number'),
      construct.Padding(8),
      construct.ULInt32('directory_strings_offset'),
      construct.Padding(68))

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

  def _ParseFilenames(self, file_object, file_information):
    """Parses the filenames.

    Args:
      file_object: A file-like object to read data from.
      file_information: The file information construct object.

    Returns:
      A list of filenames.
    """
    filenames_offset = file_information.get('filenames_offset', 0)
    filenames_size = file_information.get('filenames_size', 0)

    if filenames_offset > 0 and filenames_size > 0:
      file_object.seek(filenames_offset, os.SEEK_SET)
      filenames_data = file_object.read(filenames_size)
      filenames = binary.ArrayOfUt16StreamCopyToString(filenames_data)

    else:
      filenames = []

    return filenames

  def _ParseVolumesInformationSection(
      self, file_object, format_version, file_information):
    """Parses the volumes information section.

    Args:
      file_object: A file-like object to read data from.
      format_version: The format version.
      file_information: The file information construct object.

    Yields:
      A volume information construct object.
    """
    volumes_information_offset = file_information.get(
        'volumes_information_offset', 0)

    if volumes_information_offset > 0:
      number_of_volumes = file_information.get('number_of_volumes', 0)
      file_object.seek(volumes_information_offset, os.SEEK_SET)

      while number_of_volumes > 0:
        try:
          if format_version == 17:
            yield self.VOLUME_INFORMATION_V17.parse_stream(file_object)
          else:
            yield self.VOLUME_INFORMATION_V23.parse_stream(file_object)
        except (IOError, construct.FieldError) as exception:
          raise errors.UnableToParseFile((
              u'Unable to parse volume information v{0:d} with error: '
              u'{1:s}').format(format_version, exception))

        number_of_volumes -= 1

  def _ParseVolumeDevicePath(
      self, file_object, file_information, volume_information):
    """Parses the volume device path.

    This function expects the current offset of the file-like object to point
    as the end of the volume information structure.

    Args:
      file_object: A file-like object to read data from.
      file_information: The file information construct object.
      volume_information: The volume information construct object.

    Returns:
      A Unicode string containing the device path or None if not available.
    """
    volumes_information_offset = file_information.get(
        'volumes_information_offset', 0)

    device_path = None
    if volumes_information_offset > 0:
      device_path_offset = volume_information.get('device_path_offset', 0)
      device_path_size = 2 * volume_information.get(
          'device_path_number_of_characters', 0)

      if device_path_offset >= 36 and device_path_size > 0:
        device_path_offset += volumes_information_offset
        file_object.seek(device_path_offset, os.SEEK_SET)

        device_path = binary.ReadUtf16Stream(
            file_object, byte_size=device_path_size)

    return device_path

  def Parse(self, file_entry):
    """Extracts events from a Windows Prefetch file.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      Event objects (instances of EventObject) of the extracted events.
    """
    file_object = file_entry.GetFileObject()
    file_header = self._ParseFileHeader(file_object)

    format_version = file_header.get('version', None)
    if format_version not in [17, 23, 26]:
      raise errors.UnableToParseFile(
          u'Unsupported format version: {0:d}'.format(format_version))

    file_information = self._ParseFileInformation(file_object, format_version)
    mapped_files = self._ParseFilenames(file_object, file_information)

    container = WinPrefetchExecutionEventContainer(
        file_header, file_information, mapped_files)

    executable = binary.Ut16StreamCopyToString(
        file_header.get('executable', u''))

    for volume_information in self._ParseVolumesInformationSection(
        file_object, format_version, file_information):
      volume_serial_number = volume_information.get('serial_number', 0)
      volume_device_path = self._ParseVolumeDevicePath(
          file_object, file_information, volume_information)

      container.AppendVolume(volume_serial_number, volume_device_path)

      timestamp = volume_information.get('creation_time', 0)
      if timestamp:
        container.Append(event.FiletimeEvent(
            timestamp, eventdata.EventTimestamp.CREATION_TIME,
            container.data_type))

      for mapped_file in mapped_files:
        if mapped_file.endswith(executable):
          _, _, container.path = mapped_file.partition(volume_device_path)

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

    file_object.close()
    yield container
