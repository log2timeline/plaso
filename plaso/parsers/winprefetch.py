"""Parser for Windows Prefetch files."""

import os

import pyfwnt
import pyscca

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import windows_events
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinPrefetchExecutionEventData(events.EventData):
    """Windows Prefetch event data.

    Attributes:
      executable (str): executable filename.
      last_run_time (dfdatetime.DateTimeValues): executable (binary) last run date and
          time.
      mapped_files (list[str]): mapped filenames.
      number_of_volumes (int): number of volumes.
      path_hints (list[str]): possible full paths to the executable.
      prefetch_hash (int): prefetch hash.
      previous_run_times (list[dfdatetime.DateTimeValues]): previous executable (binary)
          run date and time.
      run_count (int): run count.
      version (int): format version.
      volume_device_paths (list[str]): volume device paths.
      volume_serial_numbers (list[int]): volume serial numbers.
    """

    DATA_TYPE = "windows:prefetch:execution"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
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

    # Number of bytes of compressed data read to determine the signature of the
    # uncompressed data.
    _COMPRESSED_DATA_READ_SIZE = 4096

    NAME = "prefetch"
    DATA_FORMAT = "Windows Prefetch File (PF)"

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification.

        Returns:
          FormatSpecification: format specification.
        """
        format_specification = specification.FormatSpecification(cls.NAME)
        format_specification.AddNewSignature(b"SCCA", offset=4)
        format_specification.AddNewSignature(b"MAM\x04", offset=0)
        return format_specification

    def _CheckCompressedSignature(self, file_object):
        """Checks the signature of a MAM compressed file.

        Files other than Windows Prefetch files, such as Emergency Boot Disk (EBD)
        files, can be compressed using the same MAM compressed format.

        Args:
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: if the uncompressed data does not contain a Windows Prefetch
              file signature.
        """
        file_object.seek(0, os.SEEK_SET)
        compressed_data = file_object.read(8 + self._COMPRESSED_DATA_READ_SIZE)

        if compressed_data[:4] == b"MAM\x04" and len(compressed_data) > 8:
            try:
                uncompressed_data = pyfwnt.lzxpress_huffman_decompress(
                    compressed_data[8:], 8
                )
            except OSError:
                # Errors are reported when the file is opened by pyscca.
                uncompressed_data = None

            if uncompressed_data and uncompressed_data[4:8] != b"SCCA":
                raise errors.WrongParser(
                    "Unsupported signature in MAM compressed data."
                )

        file_object.seek(0, os.SEEK_SET)

    def _ParseSCCAFile(self, parser_mediator, scca_file):
        """Parses a Windows Prefetch (SCCA) file.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          scca_file (pyscca.file): Windows Prefetch (SCCA) file

        Raises:
          OSError: if the Windows Prefetch (SCCA) file cannot be parsed.
        """
        format_version = scca_file.format_version
        executable_filename = scca_file.executable_filename
        executable_filename_lower = executable_filename.lower()
        executable_filename_length = len(executable_filename)
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
                    timestamp=timestamp
                )
                event_data.device_path = volume_device_path
                event_data.origin = parser_mediator.GetFilename()
                event_data.serial_number = volume_serial_number

                parser_mediator.ProduceEventData(event_data)

            volume_device_path_length = len(volume_device_path)
            for filename in iter(scca_file.filenames):
                if not filename or not filename.startswith(volume_device_path):
                    continue

                path = filename[volume_device_path_length:]
                _, _, basename = path.rpartition("\\")
                basename_lower = basename.lower()
                if executable_filename_length == 29 and basename_lower.startswith(
                    executable_filename_lower
                ):
                    path_hints.append(path)
                elif basename_lower == executable_filename_lower:
                    path_hints.append(path)

        mapped_files = []
        for entry_index, file_metrics in enumerate(scca_file.file_metrics_entries):
            mapped_file_string = file_metrics.filename
            if not mapped_file_string:
                # Note given this is a lookup error not treating it as corruption
                # scenario.
                parser_mediator.ProduceWarning(
                    f"missing filename for file metrics entry: {entry_index:d}"
                )
                continue

            file_reference = file_metrics.file_reference
            if file_reference:
                mft_entry_index = file_reference & 0xFFFFFFFFFFFF
                sequence_number = file_reference >> 48
                mapped_file_string = (
                    f"{mapped_file_string:s} [{mft_entry_index:d}-{sequence_number:d}]"
                )

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
            event_data.last_run_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

        # Check for the 7 older last run time values available since format version 26.
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
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        self._CheckCompressedSignature(file_object)

        scca_file = pyscca.file()

        try:
            scca_file.open_file_object(file_object)
        except OSError as exception:
            parser_mediator.ProduceWarning(
                f"unable to open file with error: {exception!s}"
            )
            return

        try:
            self._ParseSCCAFile(parser_mediator, scca_file)
        except OSError as exception:
            parser_mediator.ProduceWarning(
                f"unable to parse file with error: {exception!s}"
            )
        finally:
            scca_file.close()


manager.ParsersManager.RegisterParser(WinPrefetchParser)
