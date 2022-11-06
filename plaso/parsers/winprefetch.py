# -*- coding: utf-8 -*-
"""Parser for Windows Prefetch files."""

import pyscca

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import windows_events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinPrefetchExecutionEventData(events.EventData):
  """Windows Prefetch event data.

  Attributes:
    executable (str): executable filename.
    format_version (int): format version.
    last_run_time (dfdatetime.DateTimeValues): executable (binary) last run
        date and time.
    mapped_files (list[str]): mapped filenames.
    number_of_volumes (int): number of volumes.
    path_hints (list[str]): possible full paths to the executable.
    prefetch_hash (int): prefetch hash.
    previous_run_times (list[dfdatetime.DateTimeValues]): previous executable
        (binary) run date and time.
    run_count (int): run count.
    volume_device_paths (list[str]): volume device paths.
    volume_serial_numbers (list[int]): volume serial numbers.
  """

  DATA_TYPE = 'windows:prefetch:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinPrefetchExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.executable = None
    self.last_run_time = None
    self.mapped_files = None
    self.number_of_volumes = None
    self.path_hints = None
    self.prefetch_hash = None
    self.previous_run_times = None
    self.run_count = None
    self.version = None
    self.volume_device_paths = None
    self.volume_serial_numbers = None


class WinPrefetchParser(interface.FileObjectParser):
  """A parser for Windows Prefetch files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'prefetch'
  DATA_FORMAT = 'Windows Prefetch File (PF)'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'SCCA', offset=4)
    format_specification.AddNewSignature(b'MAM\x04', offset=0)
    return format_specification

  def _ParseSCCAFile(self, parser_mediator, scca_file):
    """Parses a Windows Prefetch (SCCA) file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      scca_file (pyscca.file): Windows Prefetch (SCCA) file

    Raises:
      IOError: if the Windows Prefetch (SCCA) file cannot be parsed.
    """
    format_version = scca_file.format_version
    executable_filename = scca_file.executable_filename
    prefetch_hash = scca_file.prefetch_hash
    run_count = scca_file.run_count
    number_of_volumes = scca_file.number_of_volumes

    volume_serial_numbers = []
    volume_device_paths = []
    path_hints = []

    for volume_information in iter(scca_file.volumes):
      volume_serial_number = volume_information.serial_number
      volume_device_path = volume_information.device_path

      volume_serial_numbers.append(volume_serial_number)
      volume_device_paths.append(volume_device_path)

      timestamp = volume_information.get_creation_time_as_integer()
      if timestamp:
        event_data = windows_events.WindowsVolumeEventData()
        event_data.creation_time = dfdatetime_filetime.Filetime(
            timestamp=timestamp)
        event_data.device_path = volume_device_path
        event_data.origin = parser_mediator.GetFilename()
        event_data.serial_number = volume_serial_number

        parser_mediator.ProduceEventData(event_data)

      for filename in iter(scca_file.filenames):
        if not filename:
          continue

        if (filename.startswith(volume_device_path) and
            filename.endswith(executable_filename)):
          _, _, path = filename.partition(volume_device_path)
          path_hints.append(path)

    mapped_files = []
    for entry_index, file_metrics in enumerate(scca_file.file_metrics_entries):
      mapped_file_string = file_metrics.filename
      if not mapped_file_string:
        parser_mediator.ProduceExtractionWarning(
            'missing filename for file metrics entry: {0:d}'.format(
                entry_index))
        continue

      file_reference = file_metrics.file_reference
      if file_reference:
        mapped_file_string = (
            '{0:s} [{1:d}-{2:d}]').format(
                mapped_file_string, file_reference & 0xffffffffffff,
                file_reference >> 48)

      mapped_files.append(mapped_file_string)

    event_data = WinPrefetchExecutionEventData()
    event_data.executable = executable_filename
    event_data.mapped_files = mapped_files
    event_data.number_of_volumes = number_of_volumes
    event_data.path_hints = path_hints
    event_data.prefetch_hash = prefetch_hash
    event_data.run_count = run_count
    event_data.version = format_version
    event_data.volume_device_paths = volume_device_paths
    event_data.volume_serial_numbers = volume_serial_numbers

    timestamp = scca_file.get_last_run_time_as_integer(0)
    if timestamp:
      event_data.last_run_time = dfdatetime_filetime.Filetime(
          timestamp=timestamp)

    # Check for the 7 older last run time values available since
    # format version 26.
    if format_version >= 26:
      previous_run_times = []
      for last_run_time_index in range(1, 8):
        timestamp = scca_file.get_last_run_time_as_integer(last_run_time_index)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          previous_run_times.append(date_time)

      if previous_run_times:
        event_data.previous_run_times = previous_run_times

    parser_mediator.ProduceEventData(event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Prefetch file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.
    """
    scca_file = pyscca.file()

    try:
      scca_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    try:
      self._ParseSCCAFile(parser_mediator, scca_file)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse file with error: {0!s}'.format(exception))
    finally:
      scca_file.close()


manager.ParsersManager.RegisterParser(WinPrefetchParser)
