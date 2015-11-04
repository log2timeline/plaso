# -*- coding: utf-8 -*-
"""Parser for Windows Prefetch files."""

import logging
import os

import construct

from plaso.events import time_events
from plaso.events import windows_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinPrefetchExecutionEvent(time_events.FiletimeEvent):
  """Class that defines a Windows Prefetch execution event."""

  DATA_TYPE = u'windows:prefetch:execution'

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

    self.version = file_header.get(u'version', None)
    self.executable = binary.Utf16StreamCopyToString(
        file_header.get(u'executable', u''))
    self.prefetch_hash = file_header.get(u'prefetch_hash', None)

    self.run_count = file_information.get(u'run_count', None)
    self.mapped_files = mapped_files
    self.path = path

    self.number_of_volumes = file_information.get(u'number_of_volumes', 0)
    self.volume_serial_numbers = volume_serial_numbers
    self.volume_device_paths = volume_device_paths


class WinPrefetchParser(interface.FileObjectParser):
  """A parser for Windows Prefetch files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'prefetch'
  DESCRIPTION = u'Parser for Windows Prefetch files.'

  _FILE_SIGNATURE = b'SCCA'

  _FILE_HEADER_STRUCT = construct.Struct(
      u'file_header',
      construct.ULInt32(u'version'),
      construct.String(u'signature', 4),
      construct.Padding(4),
      construct.ULInt32(u'file_size'),
      construct.String(u'executable', 60),
      construct.ULInt32(u'prefetch_hash'),
      construct.ULInt32(u'flags'))

  _FILE_INFORMATION_V17 = construct.Struct(
      u'file_information_v17',
      construct.ULInt32(u'metrics_array_offset'),
      construct.ULInt32(u'number_of_metrics_array_entries'),
      construct.ULInt32(u'trace_chains_array_offset'),
      construct.ULInt32(u'number_of_trace_chains_array_entries'),
      construct.ULInt32(u'filename_strings_offset'),
      construct.ULInt32(u'filename_strings_size'),
      construct.ULInt32(u'volumes_information_offset'),
      construct.ULInt32(u'number_of_volumes'),
      construct.ULInt32(u'volumes_information_size'),
      construct.ULInt64(u'last_run_time'),
      construct.Padding(16),
      construct.ULInt32(u'run_count'),
      construct.Padding(4))

  _FILE_INFORMATION_V23 = construct.Struct(
      u'file_information_v23',
      construct.ULInt32(u'metrics_array_offset'),
      construct.ULInt32(u'number_of_metrics_array_entries'),
      construct.ULInt32(u'trace_chains_array_offset'),
      construct.ULInt32(u'number_of_trace_chains_array_entries'),
      construct.ULInt32(u'filename_strings_offset'),
      construct.ULInt32(u'filename_strings_size'),
      construct.ULInt32(u'volumes_information_offset'),
      construct.ULInt32(u'number_of_volumes'),
      construct.ULInt32(u'volumes_information_size'),
      construct.Padding(8),
      construct.ULInt64(u'last_run_time'),
      construct.Padding(16),
      construct.ULInt32(u'run_count'),
      construct.Padding(84))

  _FILE_INFORMATION_V26 = construct.Struct(
      u'file_information_v26',
      construct.ULInt32(u'metrics_array_offset'),
      construct.ULInt32(u'number_of_metrics_array_entries'),
      construct.ULInt32(u'trace_chains_array_offset'),
      construct.ULInt32(u'number_of_trace_chains_array_entries'),
      construct.ULInt32(u'filename_strings_offset'),
      construct.ULInt32(u'filename_strings_size'),
      construct.ULInt32(u'volumes_information_offset'),
      construct.ULInt32(u'number_of_volumes'),
      construct.ULInt32(u'volumes_information_size'),
      construct.Padding(8),
      construct.ULInt64(u'last_run_time'),
      construct.ULInt64(u'last_run_time1'),
      construct.ULInt64(u'last_run_time2'),
      construct.ULInt64(u'last_run_time3'),
      construct.ULInt64(u'last_run_time4'),
      construct.ULInt64(u'last_run_time5'),
      construct.ULInt64(u'last_run_time6'),
      construct.ULInt64(u'last_run_time7'),
      construct.Padding(16),
      construct.ULInt32(u'run_count'),
      construct.Padding(96))

  _METRICS_ARRAY_ENTRY_V17 = construct.Struct(
      u'metrics_array_entry_v17',
      construct.ULInt32(u'start_time'),
      construct.ULInt32(u'duration'),
      construct.ULInt32(u'filename_string_offset'),
      construct.ULInt32(u'filename_string_number_of_characters'),
      construct.Padding(4))

  # Note that at the moment for the purpose of this parser
  # the v23 and v26 metrics array entry structures are the same.
  _METRICS_ARRAY_ENTRY_V23 = construct.Struct(
      u'metrics_array_entry_v23',
      construct.ULInt32(u'start_time'),
      construct.ULInt32(u'duration'),
      construct.ULInt32(u'average_duration'),
      construct.ULInt32(u'filename_string_offset'),
      construct.ULInt32(u'filename_string_number_of_characters'),
      construct.Padding(4),
      construct.ULInt64(u'file_reference'))

  _VOLUME_INFORMATION_V17 = construct.Struct(
      u'volume_information_v17',
      construct.ULInt32(u'device_path_offset'),
      construct.ULInt32(u'device_path_number_of_characters'),
      construct.ULInt64(u'creation_time'),
      construct.ULInt32(u'serial_number'),
      construct.Padding(8),
      construct.ULInt32(u'directory_strings_offset'),
      construct.ULInt32(u'number_of_directory_strings'),
      construct.Padding(4))

  # Note that at the moment for the purpose of this parser
  # the v23 and v26 volume information structures are the same.
  _VOLUME_INFORMATION_V23 = construct.Struct(
      u'volume_information_v23',
      construct.ULInt32(u'device_path_offset'),
      construct.ULInt32(u'device_path_number_of_characters'),
      construct.ULInt64(u'creation_time'),
      construct.ULInt32(u'serial_number'),
      construct.Padding(8),
      construct.ULInt32(u'directory_strings_offset'),
      construct.ULInt32(u'number_of_directory_strings'),
      construct.Padding(68))

  def _ParseFileHeader(self, file_object):
    """Parses the file header.

    Args:
      file_object: A file-like object to read data from.

    Returns:
      The file header construct object.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    try:
      file_header = self._FILE_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse file header with error: {0:s}'.format(exception))

    if not file_header:
      raise errors.UnableToParseFile(u'Unable to read file header')

    if file_header.get(u'signature', None) != self._FILE_SIGNATURE:
      raise errors.UnableToParseFile(u'Unsupported file signature')

    return file_header

  def _ParseFileInformation(self, file_object, format_version):
    """Parses the file information.

    Args:
      file_object: A file-like object to read data from.
      format_version: The format version.

    Returns:
      The file information construct object.

    Raises:
      UnableToParseFile: when the file information cannot be parsed.
    """
    try:
      if format_version == 17:
        file_information = self._FILE_INFORMATION_V17.parse_stream(file_object)
      elif format_version == 23:
        file_information = self._FILE_INFORMATION_V23.parse_stream(file_object)
      elif format_version == 26:
        file_information = self._FILE_INFORMATION_V26.parse_stream(file_object)
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

    Raises:
      UnableToParseFile: when the metrics array cannot be parsed.
    """
    metrics_array = []

    metrics_array_offset = file_information.get(u'metrics_array_offset', 0)
    number_of_metrics_array_entries = file_information.get(
        u'number_of_metrics_array_entries', 0)

    if metrics_array_offset > 0 and number_of_metrics_array_entries > 0:
      file_object.seek(metrics_array_offset, os.SEEK_SET)

      for entry_index in range(0, number_of_metrics_array_entries):
        try:
          if format_version == 17:
            metrics_array_entry = self._METRICS_ARRAY_ENTRY_V17.parse_stream(
                file_object)
          elif format_version in [23, 26]:
            metrics_array_entry = self._METRICS_ARRAY_ENTRY_V23.parse_stream(
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
    filename_strings_offset = file_information.get(
        u'filename_strings_offset', 0)
    filename_strings_size = file_information.get(u'filename_strings_size', 0)

    if filename_strings_offset > 0 and filename_strings_size > 0:
      file_object.seek(filename_strings_offset, os.SEEK_SET)
      filename_strings_data = file_object.read(filename_strings_size)
      filename_strings = binary.ArrayOfUtf16StreamCopyToStringTable(
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

    Raises:
      UnableToParseFile: when the volume information cannot be parsed.
    """
    volumes_information_offset = file_information.get(
        u'volumes_information_offset', 0)

    if volumes_information_offset > 0:
      number_of_volumes = file_information.get(u'number_of_volumes', 0)
      file_object.seek(volumes_information_offset, os.SEEK_SET)

      while number_of_volumes > 0:
        try:
          if format_version == 17:
            yield self._VOLUME_INFORMATION_V17.parse_stream(file_object)
          else:
            yield self._VOLUME_INFORMATION_V23.parse_stream(file_object)
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
        u'volumes_information_offset', 0)

    device_path = None
    if volumes_information_offset > 0:
      device_path_offset = volume_information.get(u'device_path_offset', 0)
      device_path_size = 2 * volume_information.get(
          u'device_path_number_of_characters', 0)

      if device_path_offset >= 36 and device_path_size > 0:
        device_path_offset += volumes_information_offset
        current_offset = file_object.tell()

        file_object.seek(device_path_offset, os.SEEK_SET)
        device_path = binary.ReadUtf16Stream(
            file_object, byte_size=device_path_size)

        file_object.seek(current_offset, os.SEEK_SET)

    return device_path

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(cls._FILE_SIGNATURE, offset=4)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Prefetch file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    file_header = self._ParseFileHeader(file_object)

    format_version = file_header.get(u'version', None)
    if format_version not in [17, 23, 26]:
      raise errors.UnableToParseFile(
          u'Unsupported format version: {0:d}'.format(format_version))

    file_information = self._ParseFileInformation(file_object, format_version)
    metrics_array = self._ParseMetricsArray(
        file_object, format_version, file_information)
    try:
      filename_strings = self._ParseFilenameStrings(
          file_object, file_information)
    except UnicodeDecodeError as exception:
      file_name = parser_mediator.GetDisplayName()
      logging.warning((
          u'[{0:s}] Unable to parse filename information from file {1:s} '
          u'with error: {2:s}').format(
              parser_mediator.GetParserChain(), file_name, exception))
      filename_strings = {}

    if len(metrics_array) != len(filename_strings):
      logging.debug(
          u'Mismatch in number of metrics and filename strings array entries.')

    executable = binary.Utf16StreamCopyToString(
        file_header.get(u'executable', u''))

    volume_serial_numbers = []
    volume_device_paths = []
    path = u''

    for volume_information in self._ParseVolumesInformationSection(
        file_object, format_version, file_information):
      volume_serial_number = volume_information.get(u'serial_number', 0)
      volume_device_path = self._ParseVolumeDevicePath(
          file_object, file_information, volume_information)

      volume_serial_numbers.append(volume_serial_number)
      volume_device_paths.append(volume_device_path)

      timestamp = volume_information.get(u'creation_time', 0)
      if timestamp:
        event_object = windows_events.WindowsVolumeCreationEvent(
            timestamp, volume_device_path, volume_serial_number,
            parser_mediator.GetFilename())
        parser_mediator.ProduceEvent(event_object)

      for filename in filename_strings.itervalues():
        if not filename:
          continue
        if (filename.startswith(volume_device_path) and
            filename.endswith(executable)):
          _, _, path = filename.partition(volume_device_path)

    mapped_files = []
    for metrics_array_entry in metrics_array:
      file_reference = metrics_array_entry.get(u'file_reference', 0)
      filename_string_offset = metrics_array_entry.get(
          u'filename_string_offset', 0)

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

    timestamp = file_information.get(u'last_run_time', 0)
    if timestamp:
      event_object = WinPrefetchExecutionEvent(
          timestamp, eventdata.EventTimestamp.LAST_RUNTIME, file_header,
          file_information, mapped_files, path, volume_serial_numbers,
          volume_device_paths)
      parser_mediator.ProduceEvent(event_object)

    # Check for the 7 older last run time values available in v26.
    if format_version == 26:
      for last_run_time_index in range(1, 8):
        last_run_time_identifier = u'last_run_time{0:d}'.format(
            last_run_time_index)

        timestamp = file_information.get(last_run_time_identifier, 0)
        if timestamp:
          event_object = WinPrefetchExecutionEvent(
              timestamp,
              u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME),
              file_header, file_information, mapped_files, path,
              volume_serial_numbers, volume_device_paths)
          parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(WinPrefetchParser)
