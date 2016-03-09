# -*- coding: utf-8 -*-
"""Parser for Windows Prefetch files."""

import pyscca

from plaso import dependencies
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


dependencies.CheckModuleVersion(u'pyscca')


class WinPrefetchExecutionEvent(time_events.FiletimeEvent):
  """Class that defines a Windows Prefetch execution event.

  Attributes:
    executable: a string containing the executable filename.
    format_version: an integer containing the format version.
    mapped_files: a list of strings containing the mapped filenames.
    number_of_volumes: an integer containing the number of volumes.
    path: a path to the executable.
    prefetch_hash: an integer containing the prefetch hash.
    run_count: an integer containing the run count.
    volume_device_paths: a list of strings containing volume device path
                         strings.
    volume_serial_numbers: a list of integers containing the volume serial
                           numbers.
  """

  DATA_TYPE = u'windows:prefetch:execution'

  def __init__(
      self, timestamp, timestamp_description, format_version,
      executable_filename, prefetch_hash, run_count, mapped_files, path,
      number_of_volumes, volume_serial_numbers, volume_device_paths):
    """Initializes the event.

    Args:
      timestamp: the FILETIME timestamp value.
      timestamp_description: the usage string for the timestamp value.
      format_version: an integer containing the format version.
      executable_filename: a string containing the executable filename.
      prefetch_hash: an integer containing the prefetch hash.
      run_count: an integer containing the run count.
      mapped_files: a list of strings containing the mapped filenames.
      path: a path to the executable.
      number_of_volumes: an integer containing the number of volumes.
      volume_serial_numbers: a list of integers containing volume serial
                             numbers.
      volume_device_paths: a list of strings containing volume device path
                           strings.
    """
    super(WinPrefetchExecutionEvent, self).__init__(
        timestamp, timestamp_description)
    self.executable = executable_filename
    self.mapped_files = mapped_files
    self.number_of_volumes = number_of_volumes
    self.path = path
    self.prefetch_hash = prefetch_hash
    self.run_count = run_count
    self.version = format_version
    self.volume_device_paths = volume_device_paths
    self.volume_serial_numbers = volume_serial_numbers


class WinPrefetchParser(interface.FileObjectParser):
  """A parser for Windows Prefetch files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'prefetch'
  DESCRIPTION = u'Parser for Windows Prefetch files.'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'SCCA', offset=4)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Prefetch file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    scca_file = pyscca.file()

    try:
      scca_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to open file with error: {0:s}'.format(exception))
      return

    format_version = scca_file.format_version
    executable_filename = scca_file.executable_filename
    prefetch_hash = scca_file.prefetch_hash
    run_count = scca_file.run_count
    number_of_volumes = scca_file.number_of_volumes

    volume_serial_numbers = []
    volume_device_paths = []
    path = u''

    for volume_information in scca_file.volumes:
      volume_serial_number = volume_information.serial_number
      volume_device_path = volume_information.device_path

      volume_serial_numbers.append(volume_serial_number)
      volume_device_paths.append(volume_device_path)

      timestamp = volume_information.get_creation_time_as_integer()
      if timestamp:
        event_object = windows_events.WindowsVolumeCreationEvent(
            timestamp, volume_device_path, volume_serial_number,
            parser_mediator.GetFilename())
        parser_mediator.ProduceEvent(event_object)

      for filename in scca_file.filenames:
        if not filename:
          continue

        if (filename.startswith(volume_device_path) and
            filename.endswith(executable_filename)):
          _, _, path = filename.partition(volume_device_path)

    mapped_files = []
    for entry_index, file_metrics in enumerate(scca_file.file_metrics_entries):
      mapped_file_string = file_metrics.filename
      if not mapped_file_string:
        parser_mediator.ProduceParseError(
            u'missing filename for file metrics entry: {0:d}'.format(
                entry_index))
        continue

      file_reference = file_metrics.file_reference
      if file_reference:
        mapped_file_string = (
            u'{0:s} [MFT entry: {1:d}, sequence: {2:d}]').format(
                mapped_file_string, file_reference & 0xffffffffffffL,
                file_reference >> 48)

      mapped_files.append(mapped_file_string)

    timestamp = scca_file.get_last_run_time_as_integer(0)
    if not timestamp:
      parser_mediator.ProduceParseError(u'missing last run time')
      timestamp = timelib.Timestamp.NONE_TIMESTAMP

    event_object = WinPrefetchExecutionEvent(
        timestamp, eventdata.EventTimestamp.LAST_RUNTIME, format_version,
        executable_filename, prefetch_hash, run_count, mapped_files, path,
        number_of_volumes, volume_serial_numbers, volume_device_paths)
    parser_mediator.ProduceEvent(event_object)

    # Check for the 7 older last run time values available since
    # format version 26.
    if format_version >= 26:
      for last_run_time_index in range(1, 8):
        timestamp = scca_file.get_last_run_time_as_integer(last_run_time_index)
        if not timestamp:
          continue

        timestamp_description = u'Previous {0:s}'.format(
            eventdata.EventTimestamp.LAST_RUNTIME)
        event_object = WinPrefetchExecutionEvent(
            timestamp, timestamp_description, format_version,
            executable_filename, prefetch_hash, run_count, mapped_files, path,
            number_of_volumes, volume_serial_numbers, volume_device_paths)
        parser_mediator.ProduceEvent(event_object)

    scca_file.close()


manager.ParsersManager.RegisterParser(WinPrefetchParser)
