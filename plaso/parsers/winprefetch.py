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

import logging
import os

import construct

from plaso.events import time_events
from plaso.events import windows_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface


class WinPrefetchExecutionEvent(time_events.FiletimeEvent):
  """Class that defines a Windows Prefetch execution event."""

  DATA_TYPE = 'windows:prefetch:execution'

  def __init__(
      self, timestamp, timestamp_description, file_header, file_information,
      mapped_files, path, volume_serial_numbers, volume_device_paths):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      timestamp_description: The usage string for the timestamp value.
      file_header: The file header construct object.
      file_information: The file information construct object.
      mapped_files: A list of the mapped filenames.
      path: A path to the executable.
      volume_serial_numbers: A list of volume serial number strings.
      volume_device_paths: A list of volume device path strings.
    """
    super(WinPrefetchExecutionEvent, self).__init__(
        timestamp, timestamp_description)

    self.offset = 0

    self.version = file_header.get('version', None)
    self.executable = binary.Ut16StreamCopyToString(
        file_header.get('executable', ''))
    self.prefetch_hash = file_header.get('prefetch_hash', None)

    self.run_count = file_information.get('run_count', None)
    self.mapped_files = mapped_files
    self.path = path

    self.number_of_volumes = file_information.get('number_of_volumes', 0)
    self.volume_serial_numbers = volume_serial_numbers
    self.volume_device_paths = volume_device_paths


class WinPrefetchParser(interface.BaseParser):
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
      construct.ULInt32('metrics_array_offset'),
      construct.ULInt32('number_of_metrics_array_entries'),
      construct.ULInt32('trace_chains_array_offset'),
      construct.ULInt32('number_of_trace_chains_array_entries'),
      construct.ULInt32('filename_strings_offset'),
      construct.ULInt32('filename_strings_size'),
      construct.ULInt32('volumes_information_offset'),
      construct.ULInt32('number_of_volumes'),
      construct.ULInt32('volumes_information_size'),
      construct.ULInt64('last_run_time'),
      construct.Padding(16),
      construct.ULInt32('run_count'),
      construct.Padding(4))

  FILE_INFORMATION_V23 = construct.Struct(
      'file_information_v23',
      construct.ULInt32('metrics_array_offset'),
      construct.ULInt32('number_of_metrics_array_entries'),
      construct.ULInt32('trace_chains_array_offset'),
      construct.ULInt32('number_of_trace_chains_array_entries'),
      construct.ULInt32('filename_strings_offset'),
      construct.ULInt32('filename_strings_size'),
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
      construct.ULInt32('metrics_array_offset'),
      construct.ULInt32('number_of_metrics_array_entries'),
      construct.ULInt32('trace_chains_array_offset'),
      construct.ULInt32('number_of_trace_chains_array_entries'),
      construct.ULInt32('filename_strings_offset'),
      construct.ULInt32('filename_strings_size'),
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

  METRICS_ARRAY_ENTRY_V17 = construct.Struct(
      'metrics_array_entry_v17',
      construct.ULInt32('start_time'),
      construct.ULInt32('duration'),
      construct.ULInt32('filename_string_offset'),
      construct.ULInt32('filename_string_number_of_characters'),
      construct.Padding(4))

  # Note that at the moment for the purpose of this parser
  # the v23 and v26 metrics array entry structures are the same.
  METRICS_ARRAY_ENTRY_V23 = construct.Struct(
      'metrics_array_entry_v23',
      construct.ULInt32('start_time'),
      construct.ULInt32('duration'),
      construct.ULInt32('average_duration'),
      construct.ULInt32('filename_string_offset'),
      construct.ULInt32('filename_string_number_of_characters'),
      construct.Padding(4),
      construct.ULInt64('file_reference'))

  VOLUME_INFORMATION_V17 = construct.Struct(
      'volume_information_v17',
      construct.ULInt32('device_path_offset'),
      construct.ULInt32('device_path_number_of_characters'),
      construct.ULInt64('creation_time'),
      construct.ULInt32('serial_number'),
      construct.Padding(8),
      construct.ULInt32('directory_strings_offset'),
      construct.ULInt32('number_of_directory_strings'),
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
      construct.ULInt32('number_of_directory_strings'),
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
          u'Unable to parse file header with error: {0:s}'.format(exception))

    if not file_header:
      raise errors.UnableToParseFile(u'Unable to read file header')

    if file_header.get('signature', None) != self.FILE_SIGNATURE:
      raise errors.UnableToParseFile(u'Unsupported file signature')

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
          u'Unable to parse v{0:d} file information with error: {1:s}'.format(
              format_version, exception))

    if not file_information:
      raise errors.UnableToParseFile(
          u'Unable to read v{0:d} file information'.format(format_version))
    return file_information

  def _ParseMetricsArray(self, file_object, format_version, file_information):
    """Parses the metrics array.

    Args:
      file_object: A file-like object to read data from.
      format_version: The format version.
      file_information: The file information construct object.

    Returns:
      A list of metrics array entry construct objects.
    """
    metrics_array = []

    metrics_array_offset = file_information.get('metrics_array_offset', 0)
    number_of_metrics_array_entries = file_information.get(
        'number_of_metrics_array_entries', 0)

    if metrics_array_offset > 0 and number_of_metrics_array_entries > 0:
      file_object.seek(metrics_array_offset, os.SEEK_SET)

      for entry_index in range(0, number_of_metrics_array_entries):
        try:
          if format_version == 17:
            metrics_array_entry = self.METRICS_ARRAY_ENTRY_V17.parse_stream(
                file_object)
          elif format_version in [23, 26]:
            metrics_array_entry = self.METRICS_ARRAY_ENTRY_V23.parse_stream(
                file_object)
          else:
            metrics_array_entry = None
        except (IOError, construct.FieldError) as exception:
          raise errors.UnableToParseFile((
              u'Unable to parse v{0:d} metrics array entry: {1:d} with error: '
              u'{2:s}').format(format_version, entry_index, exception))

        if not metrics_array_entry:
          raise errors.UnableToParseFile(
              u'Unable to read v{0:d} metrics array entry: {1:d}'.format(
                  format_version, entry_index))

        metrics_array.append(metrics_array_entry)

    return metrics_array

  def _ParseFilenameStrings(self, file_object, file_information):
    """Parses the filename strings.

    Args:
      file_object: A file-like object to read data from.
      file_information: The file information construct object.

    Returns:
      A dict of filename strings with their byte offset as the key.
    """
    filename_strings_offset = file_information.get('filename_strings_offset', 0)
    filename_strings_size = file_information.get('filename_strings_size', 0)

    if filename_strings_offset > 0 and filename_strings_size > 0:
      file_object.seek(filename_strings_offset, os.SEEK_SET)
      filename_strings_data = file_object.read(filename_strings_size)
      filename_strings = binary.ArrayOfUt16StreamCopyToStringTable(
          filename_strings_data)

    else:
      filename_strings = {}

    return filename_strings

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
              u'Unable to parse v{0:d} volume information with error: '
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
        current_offset = file_object.tell()

        file_object.seek(device_path_offset, os.SEEK_SET)
        device_path = binary.ReadUtf16Stream(
            file_object, byte_size=device_path_size)

        file_object.seek(current_offset, os.SEEK_SET)

    return device_path

  def Parse(self, parser_context, file_entry):
    """Extracts events from a Windows Prefetch file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
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
    metrics_array = self._ParseMetricsArray(
        file_object, format_version, file_information)
    filename_strings = self._ParseFilenameStrings(file_object, file_information)

    if len(metrics_array) != len(filename_strings):
      logging.debug(
          u'Mismatch in number of metrics and filename strings array entries.')

    executable = binary.Ut16StreamCopyToString(
        file_header.get('executable', u''))

    volume_serial_numbers = []
    volume_device_paths = []
    path = u''

    for volume_information in self._ParseVolumesInformationSection(
        file_object, format_version, file_information):
      volume_serial_number = volume_information.get('serial_number', 0)
      volume_device_path = self._ParseVolumeDevicePath(
          file_object, file_information, volume_information)

      volume_serial_numbers.append(volume_serial_number)
      volume_device_paths.append(volume_device_path)

      timestamp = volume_information.get('creation_time', 0)
      if timestamp:
        event_object = windows_events.WindowsVolumeCreationEvent(
            timestamp, volume_device_path, volume_serial_number,
            file_entry.name)
        parser_context.ProduceEvent(
            event_object, parser_name=self.NAME, file_entry=file_entry)

      for filename in filename_strings.itervalues():
        if (filename.startswith(volume_device_path) and
            filename.endswith(executable)):
          _, _, path = filename.partition(volume_device_path)

    mapped_files = []
    for metrics_array_entry in metrics_array:
      file_reference = metrics_array_entry.get('file_reference', 0)
      filename_string_offset = metrics_array_entry.get(
          'filename_string_offset', 0)

      filename = filename_strings.get(filename_string_offset, u'')
      if not filename:
        logging.debug(u'Missing filename string for offset: {0:d}.'.format(
            filename_string_offset))
        continue

      if file_reference:
        mapped_file_string = (
            u'{0:s} [MFT entry: {1:d}, sequence: {2:d}]').format(
                filename, file_reference & 0xffffffffffffL,
                file_reference >> 48)
      else:
        mapped_file_string = filename

      mapped_files.append(mapped_file_string)

    timestamp = file_information.get('last_run_time', 0)
    if timestamp:
      event_object = WinPrefetchExecutionEvent(
          timestamp, eventdata.EventTimestamp.LAST_RUNTIME, file_header,
          file_information, mapped_files, path, volume_serial_numbers,
          volume_device_paths)
      parser_context.ProduceEvent(
          event_object, parser_name=self.NAME, file_entry=file_entry)

    # Check for the 7 older last run time values available in v26.
    if format_version == 26:
      for last_run_time_index in range(1, 8):
        last_run_time_identifier = 'last_run_time{0:d}'.format(
            last_run_time_index)

        timestamp = file_information.get(last_run_time_identifier, 0)
        if timestamp:
          event_object = WinPrefetchExecutionEvent(
              timestamp,
              u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME),
              file_header, file_information, mapped_files, path,
              volume_serial_numbers, volume_device_paths)
          parser_context.ProduceEvent(
              event_object, parser_name=self.NAME, file_entry=file_entry)

    file_object.close()
