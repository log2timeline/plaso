# -*- coding: utf-8 -*-
"""The status view."""

from __future__ import unicode_literals

import ctypes
import sys
import time

try:
  import win32api
  import win32console
except ImportError:
  win32console = None

from dfvfs.lib import definitions as dfvfs_definitions

import plaso

from plaso.lib import definitions
from plaso.cli import tools
from plaso.cli import views


class StatusView(object):
  """Processing status view."""

  MODE_LINEAR = 'linear'
  MODE_WINDOW = 'window'

  _SOURCE_TYPES = {
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY: 'directory',
      dfvfs_definitions.SOURCE_TYPE_FILE: 'single file',
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE: (
          'storage media device'),
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE: (
          'storage media image')}

  _UNITS_1024 = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'EiB', 'ZiB', 'YiB']

  _WINAPI_STD_OUTPUT_HANDLE = -11

  _WINAPI_ENABLE_PROCESSED_INPUT = 1
  _WINAPI_ENABLE_LINE_INPUT = 2
  _WINAPI_ENABLE_ECHO_INPUT = 4

  _WINAPI_ANSI_CONSOLE_MODE = (
      _WINAPI_ENABLE_PROCESSED_INPUT | _WINAPI_ENABLE_LINE_INPUT |
      _WINAPI_ENABLE_ECHO_INPUT)

  def __init__(self, output_writer, tool_name):
    """Initializes a status view.

    Args:
      output_writer (OutputWriter): output writer.
      tool_name (str): namd of the tool.
    """
    super(StatusView, self).__init__()
    self._artifact_filters = None
    self._filter_file = None
    self._have_ansi_support = not win32console
    self._mode = self.MODE_WINDOW
    self._output_writer = output_writer
    self._source_path = None
    self._source_type = None
    self._stdout_output_writer = isinstance(
        output_writer, tools.StdoutOutputWriter)
    self._storage_file_path = None
    self._tool_name = tool_name

    if win32console:
      kernel32 = ctypes.windll.kernel32
      stdout_handle = kernel32.GetStdHandle(self._WINAPI_STD_OUTPUT_HANDLE)
      result = kernel32.SetConsoleMode(
          stdout_handle, self._WINAPI_ANSI_CONSOLE_MODE)
      self._have_ansi_support = result != 0

  def _AddsAnalysisProcessStatusTableRow(self, process_status, table_view):
    """Adds an analysis process status table row.

    Args:
      process_status (ProcessStatus): processing status.
      table_view (CLITabularTableView): table view.
    """
    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)

    events = ''
    if (process_status.number_of_consumed_events is not None and
        process_status.number_of_consumed_events_delta is not None):
      events = '{0:d} ({1:d})'.format(
          process_status.number_of_consumed_events,
          process_status.number_of_consumed_events_delta)

    event_tags = ''
    if (process_status.number_of_produced_event_tags is not None and
        process_status.number_of_produced_event_tags_delta is not None):
      event_tags = '{0:d} ({1:d})'.format(
          process_status.number_of_produced_event_tags,
          process_status.number_of_produced_event_tags_delta)

    reports = ''
    if (process_status.number_of_produced_reports is not None and
        process_status.number_of_produced_reports_delta is not None):
      reports = '{0:d} ({1:d})'.format(
          process_status.number_of_produced_reports,
          process_status.number_of_produced_reports_delta)

    table_view.AddRow([
        process_status.identifier, process_status.pid, process_status.status,
        used_memory, events, event_tags, reports])

  def _AddExtractionProcessStatusTableRow(self, process_status, table_view):
    """Adds an extraction process status table row.

    Args:
      process_status (ProcessStatus): processing status.
      table_view (CLITabularTableView): table view.
    """
    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)

    sources = ''
    if (process_status.number_of_produced_sources is not None and
        process_status.number_of_produced_sources_delta is not None):
      sources = '{0:d} ({1:d})'.format(
          process_status.number_of_produced_sources,
          process_status.number_of_produced_sources_delta)

    events = ''
    if (process_status.number_of_produced_events is not None and
        process_status.number_of_produced_events_delta is not None):
      events = '{0:d} ({1:d})'.format(
          process_status.number_of_produced_events,
          process_status.number_of_produced_events_delta)

    # TODO: shorten display name to fit in 80 chars and show the filename.

    table_view.AddRow([
        process_status.identifier, process_status.pid, process_status.status,
        used_memory, sources, events, process_status.display_name])

  def _ClearScreen(self):
    """Clears the terminal/console screen."""
    if self._have_ansi_support:
      # ANSI escape sequence to clear screen.
      self._output_writer.Write('\033[2J')
      # ANSI escape sequence to move cursor to top left.
      self._output_writer.Write('\033[H')

    elif win32console:
      # This version of Windows cmd.exe does not support ANSI escape codes, thus
      # instead we fill the console screen buffer with spaces. The downside of
      # this approach is an annoying flicker.
      top_left_coordinate = win32console.PyCOORDType(0, 0)
      screen_buffer = win32console.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
      screen_buffer_information = screen_buffer.GetConsoleScreenBufferInfo()

      screen_buffer_attributes = screen_buffer_information['Attributes']
      screen_buffer_size = screen_buffer_information['Size']
      console_size = screen_buffer_size.X * screen_buffer_size.Y

      screen_buffer.FillConsoleOutputCharacter(
          ' ', console_size, top_left_coordinate)
      screen_buffer.FillConsoleOutputAttribute(
          screen_buffer_attributes, console_size, top_left_coordinate)
      screen_buffer.SetConsoleCursorPosition(top_left_coordinate)

      # TODO: remove update flicker. For win32console we could set the cursor
      # top left, write the table, clean the remainder of the screen buffer
      # and set the cursor at the end of the table.

  def _FormatSizeInUnitsOf1024(self, size):
    """Represents a number of bytes in units of 1024.

    Args:
      size (int): size in bytes.

    Returns:
      str: human readable string of the size.
    """
    magnitude_1024 = 0
    used_memory_1024 = float(size)
    while used_memory_1024 >= 1024:
      used_memory_1024 /= 1024
      magnitude_1024 += 1

    if 0 < magnitude_1024 <= 7:
      return '{0:.1f} {1:s}'.format(
          used_memory_1024, self._UNITS_1024[magnitude_1024])

    return '{0:d} B'.format(size)

  def _PrintAnalysisStatusHeader(self, processing_status):
    """Prints the analysis status header.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    self._output_writer.Write(
        'Storage file\t\t: {0:s}\n'.format(self._storage_file_path))

    self._PrintProcessingTime(processing_status)

    if processing_status and processing_status.events_status:
      self._PrintEventsStatus(processing_status.events_status)

    self._output_writer.Write('\n')

  def _PrintAnalysisStatusUpdateLinear(self, processing_status):
    """Prints an analysis status update in linear mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    for worker_status in processing_status.workers_status:
      status_line = (
          '{0:s} (PID: {1:d}) - events consumed: {2:d} - running: '
          '{3!s}\n').format(
              worker_status.identifier, worker_status.pid,
              worker_status.number_of_consumed_events,
              worker_status.status not in definitions.ERROR_STATUS_INDICATORS)
      self._output_writer.Write(status_line)

  def _PrintAnalysisStatusUpdateWindow(self, processing_status):
    """Prints an analysis status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    output_text = 'plaso - {0:s} version {1:s}\n\n'.format(
        self._tool_name, plaso.__version__)
    self._output_writer.Write(output_text)

    self._PrintAnalysisStatusHeader(processing_status)

    table_view = views.CLITabularTableView(column_names=[
        'Identifier', 'PID', 'Status', 'Memory', 'Events', 'Tags',
        'Reports'], column_sizes=[23, 7, 15, 15, 15, 15, 0])

    self._AddsAnalysisProcessStatusTableRow(
        processing_status.foreman_status, table_view)

    for worker_status in processing_status.workers_status:
      self._AddsAnalysisProcessStatusTableRow(worker_status, table_view)

    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

    if processing_status.aborted:
      self._output_writer.Write(
          'Processing aborted - waiting for clean up.\n\n')

    if self._stdout_output_writer:
      # We need to explicitly flush stdout to prevent partial status updates.
      sys.stdout.flush()

  def _PrintExtractionStatusUpdateLinear(self, processing_status):
    """Prints an extraction status update in linear mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    for worker_status in processing_status.workers_status:
      status_line = (
          '{0:s} (PID: {1:d}) - events produced: {2:d} - file: {3:s} '
          '- running: {4!s}\n').format(
              worker_status.identifier, worker_status.pid,
              worker_status.number_of_produced_events,
              worker_status.display_name,
              worker_status.status not in definitions.ERROR_STATUS_INDICATORS)
      self._output_writer.Write(status_line)

  def _PrintExtractionStatusUpdateWindow(self, processing_status):
    """Prints an extraction status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    output_text = 'plaso - {0:s} version {1:s}\n\n'.format(
        self._tool_name, plaso.__version__)
    self._output_writer.Write(output_text)

    self.PrintExtractionStatusHeader(processing_status)

    table_view = views.CLITabularTableView(column_names=[
        'Identifier', 'PID', 'Status', 'Memory', 'Sources', 'Events',
        'File'], column_sizes=[15, 7, 15, 15, 15, 15, 0])

    self._AddExtractionProcessStatusTableRow(
        processing_status.foreman_status, table_view)

    for worker_status in processing_status.workers_status:
      self._AddExtractionProcessStatusTableRow(worker_status, table_view)

    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

    if processing_status.aborted:
      self._output_writer.Write(
          'Processing aborted - waiting for clean up.\n\n')

    # TODO: remove update flicker. For win32console we could set the cursor
    # top left, write the table, clean the remainder of the screen buffer
    # and set the cursor at the end of the table.
    if self._stdout_output_writer:
      # We need to explicitly flush stdout to prevent partial status updates.
      sys.stdout.flush()

  def _PrintEventsStatus(self, events_status):
    """Prints the status of the events.

    Args:
      events_status (EventsStatus): events status.
    """
    if events_status:
      table_view = views.CLITabularTableView(
          column_names=['Events:', 'Filtered', 'In time slice', 'Duplicates',
                        'MACB grouped', 'Total'],
          column_sizes=[15, 15, 15, 15, 15, 0])

      table_view.AddRow([
          '', events_status.number_of_filtered_events,
          events_status.number_of_events_from_time_slice,
          events_status.number_of_duplicate_events,
          events_status.number_of_macb_grouped_events,
          events_status.total_number_of_events])

      self._output_writer.Write('\n')
      table_view.Write(self._output_writer)

  def _PrintProcessingTime(self, processing_status):
    """Prints the processing time.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if not processing_status:
      processing_time = '00:00:00'
    else:
      processing_time = time.time() - processing_status.start_time
      time_struct = time.gmtime(processing_time)
      processing_time = time.strftime('%H:%M:%S', time_struct)

    self._output_writer.Write(
        'Processing time\t\t: {0:s}\n'.format(processing_time))

  def _PrintTasksStatus(self, processing_status):
    """Prints the status of the tasks.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if processing_status and processing_status.tasks_status:
      tasks_status = processing_status.tasks_status

      table_view = views.CLITabularTableView(
          column_names=['Tasks:', 'Queued', 'Processing', 'Merging',
                        'Abandoned', 'Total'],
          column_sizes=[15, 7, 15, 15, 15, 0])

      table_view.AddRow([
          '', tasks_status.number_of_queued_tasks,
          tasks_status.number_of_tasks_processing,
          tasks_status.number_of_tasks_pending_merge,
          tasks_status.number_of_abandoned_tasks,
          tasks_status.total_number_of_tasks])

      self._output_writer.Write('\n')
      table_view.Write(self._output_writer)

  def GetAnalysisStatusUpdateCallback(self):
    """Retrieves the analysis status update callback function.

    Returns:
      function: status update callback function or None if not available.
    """
    if self._mode == self.MODE_LINEAR:
      return self._PrintAnalysisStatusUpdateLinear

    if self._mode == self.MODE_WINDOW:
      return self._PrintAnalysisStatusUpdateWindow

    return None

  def GetExtractionStatusUpdateCallback(self):
    """Retrieves the extraction status update callback function.

    Returns:
      function: status update callback function or None if not available.
    """
    if self._mode == self.MODE_LINEAR:
      return self._PrintExtractionStatusUpdateLinear

    if self._mode == self.MODE_WINDOW:
      return self._PrintExtractionStatusUpdateWindow

    return None

  # TODO: refactor to protected method.
  def PrintExtractionStatusHeader(self, processing_status):
    """Prints the extraction status header.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    self._output_writer.Write(
        'Source path\t\t: {0:s}\n'.format(self._source_path))
    self._output_writer.Write(
        'Source type\t\t: {0:s}\n'.format(self._source_type))

    if self._artifact_filters:
      artifacts_string = ', '.join(self._artifact_filters)
      self._output_writer.Write('Artifact filters\t: {0:s}\n'.format(
          artifacts_string))
    if self._filter_file:
      self._output_writer.Write('Filter file\t\t: {0:s}\n'.format(
          self._filter_file))

    self._PrintProcessingTime(processing_status)
    self._PrintTasksStatus(processing_status)
    self._output_writer.Write('\n')

  def PrintExtractionSummary(self, processing_status):
    """Prints a summary of the extraction.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if not processing_status:
      self._output_writer.Write(
          'WARNING: missing processing status information.\n')

    elif not processing_status.aborted:
      if processing_status.error_path_specs:
        self._output_writer.Write('Processing completed with errors.\n')
      else:
        self._output_writer.Write('Processing completed.\n')

      number_of_warnings = (
          processing_status.foreman_status.number_of_produced_warnings)
      if number_of_warnings:
        output_text = '\n'.join([
            '',
            ('Number of warnings generated while extracting events: '
             '{0:d}.').format(number_of_warnings),
            '',
            'Use pinfo to inspect warnings in more detail.',
            ''])
        self._output_writer.Write(output_text)

      if processing_status.error_path_specs:
        output_text = '\n'.join([
            '',
            'Path specifications that could not be processed:',
            ''])
        self._output_writer.Write(output_text)
        for path_spec in processing_status.error_path_specs:
          self._output_writer.Write(path_spec.comparable)
          self._output_writer.Write('\n')

    self._output_writer.Write('\n')

  def SetMode(self, mode):
    """Sets the mode.

    Args:
      mode (str): status view mode.
    """
    self._mode = mode

  def SetSourceInformation(
      self, source_path, source_type, artifact_filters=None, filter_file=None):
    """Sets the source information.

    Args:
      source_path (str): path of the source.
      source_type (str): source type.
      artifact_filters (Optional[list[str]]): names of artifact definitions to
          use as filters.
      filter_file (Optional[str]): filter file.
    """
    self._artifact_filters = artifact_filters
    self._filter_file = filter_file
    self._source_path = source_path
    self._source_type = self._SOURCE_TYPES.get(source_type, 'UNKNOWN')

  def SetStorageFileInformation(self, storage_file_path):
    """Sets the storage file information.

    Args:
      storage_file_path (str): path to the storage file.
    """
    self._storage_file_path = storage_file_path
