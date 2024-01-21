# -*- coding: utf-8 -*-
"""The status view."""

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

from plaso.cli import tools
from plaso.cli import views
from plaso.lib import definitions


class StatusView(object):
  """Processing status view."""

  MODE_FILE = 'file'
  MODE_LINEAR = 'linear'
  MODE_WINDOW = 'window'

  _SOURCE_TYPES = {
      definitions.SOURCE_TYPE_ARCHIVE: 'archive',
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
      tool_name (str): name of the tool.
    """
    super(StatusView, self).__init__()
    self._artifact_filters = None
    self._filter_file = None
    self._have_ansi_support = not win32console
    self._mode = self.MODE_WINDOW
    self._output_writer = output_writer
    self._source_path = None
    self._source_type = None
    self._status_file = 'status.info'
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
      events = (
          f'{process_status.number_of_consumed_events:d} '
          f'({process_status.number_of_consumed_events_delta:d})')

    event_tags = ''
    if (process_status.number_of_produced_event_tags is not None and
        process_status.number_of_produced_event_tags_delta is not None):
      event_tags = (
          f'{process_status.number_of_produced_event_tags:d} '
          f'({process_status.number_of_produced_event_tags_delta:d})')

    reports = ''
    if (process_status.number_of_produced_reports is not None and
        process_status.number_of_produced_reports_delta is not None):
      reports = (
          f'{process_status.number_of_produced_reports:d} '
          f'({process_status.number_of_produced_reports_delta:d})')

    table_view.AddRow([
        process_status.identifier, process_status.pid, process_status.status,
        used_memory, events, event_tags, reports])

  def _AddExtractionProcessStatusTableRow(
      self, process_status, table_view, show_events):
    """Adds an extraction process status table row.

    Args:
      process_status (ProcessStatus): processing status.
      table_view (CLITabularTableView): table view.
      show_events (bool): True if number of events should be shown instead of
          number of event data.
    """
    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)

    sources = ''
    if (process_status.number_of_produced_sources is not None and
        process_status.number_of_produced_sources_delta is not None):
      sources = (
          f'{process_status.number_of_produced_sources:d} '
          f'({process_status.number_of_produced_sources_delta:d})')

    events_or_event_data = ''
    if show_events:
      if (process_status.number_of_produced_events is not None and
          process_status.number_of_produced_events_delta is not None):
        events_or_event_data = (
            f'{process_status.number_of_produced_events:d} '
            f'({process_status.number_of_produced_events_delta:d})')
    else:
      if (process_status.number_of_produced_event_data is not None and
          process_status.number_of_produced_event_data_delta is not None):
        events_or_event_data = (
            f'{process_status.number_of_produced_event_data:d} '
            f'({process_status.number_of_produced_event_data_delta:d})')

    # TODO: shorten display name to fit in 80 chars and show the filename.

    table_view.AddRow([
        process_status.identifier, process_status.pid, process_status.status,
        used_memory, sources, events_or_event_data,
        process_status.display_name])

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
      units = self._UNITS_1024[magnitude_1024]
      return f'{used_memory_1024:.1f} {units:s}'

    return f'{size:d} B'

  def _FormatProcessingTime(self, processing_status):
    """Formats the processing time.

    Args:
      processing_status (ProcessingStatus): processing status.

    Returns:
      str: processing time formatted as: "5 days, 12:34:56".
    """
    processing_time = 0
    if processing_status:
      processing_time = time.time() - processing_status.start_time

    processing_time, seconds = divmod(int(processing_time), 60)
    processing_time, minutes = divmod(processing_time, 60)
    days, hours = divmod(processing_time, 24)

    if days == 0:
      days_string = ''
    elif days == 1:
      days_string = '1 day, '
    else:
      days_string = f'{days:d} days, '

    return f'{days_string:s}{hours:02d}:{minutes:02d}:{seconds:02d}'

  def _PrintAnalysisStatusHeader(self, processing_status):
    """Prints the analysis status header.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    self._output_writer.Write(
        f'Storage file\t\t: {self._storage_file_path:s}\n')

    processing_time = self._FormatProcessingTime(processing_status)
    self._output_writer.Write(f'Processing time\t\t: {processing_time:s}\n')

    if processing_status and processing_status.events_status:
      self._PrintEventsStatus(processing_status.events_status)

    self._output_writer.Write('\n')

  def _GetPathSpecificationString(self, path_spec):
    """Retrieves a printable string representation of the path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: printable string representation of the path specification.
    """
    return '\n'.join([
        line.translate(definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)
        for line in path_spec.comparable.split('\n')])

  def _PrintAnalysisStatusUpdateFile(self, processing_status):
    """Prints an analysis status update in file mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if processing_status and processing_status.events_status:
      events_status = processing_status.events_status

      with open(self._status_file, 'w', encoding='utf-8') as file_object:
        file_object.write((
            f'Events: Filtered: {events_status.number_of_filtered_events:d} In '
            f'time slice: {events_status.number_of_events_from_time_slice:d} '
            f'Duplicates: {events_status.number_of_duplicate_events:d} MACB '
            f'grouped: {events_status.number_of_macb_grouped_events:d} Total: '
            f'{events_status.total_number_of_events:d}\n'))

  def _PrintAnalysisStatusUpdateLinear(self, processing_status):
    """Prints an analysis status update in linear mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    processing_time = self._FormatProcessingTime(processing_status)
    self._output_writer.Write(f'Processing time: {processing_time:s}\n')

    self._output_writer.Write((
        f'{processing_status.foreman_status.identifier:s} (PID: '
        f'{processing_status.foreman_status.pid:d}) status: '
        f'{processing_status.foreman_status.status:s}, events consumed: '
        f'{processing_status.foreman_status.number_of_consumed_events:d}\n'))

    for worker_status in processing_status.workers_status:
      self._output_writer.Write((
          f'{worker_status.identifier:s} (PID: {worker_status.pid:d}) status: '
          f'{worker_status.status:s}, events consumed: '
          f'{worker_status.number_of_consumed_events:d}\n'))

    self._output_writer.Write('\n')

  def _PrintAnalysisStatusUpdateWindow(self, processing_status):
    """Prints an analysis status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    self._output_writer.Write(
        f'plaso - {self._tool_name:s} version {plaso.__version__:s}\n\n')

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

  def _PrintExtractionStatusUpdateFile(self, processing_status):
    """Prints an extraction status update in file mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if processing_status and processing_status.tasks_status:
      tasks_status = processing_status.tasks_status

      with open(self._status_file, 'w', encoding='utf-8') as file_object:
        file_object.write((
            f'Tasks: Queued: {tasks_status.number_of_queued_tasks:d} '
            f'Processing: {tasks_status.number_of_tasks_processing:d} '
            f'Merging: {tasks_status.number_of_tasks_pending_merge:d} '
            f'Abandoned: {tasks_status.number_of_abandoned_tasks:d} '
            f'Total: {tasks_status.total_number_of_tasks:d}\n'))

  def _PrintExtractionStatusUpdateLinear(self, processing_status):
    """Prints an extraction status update in linear mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    processing_time = self._FormatProcessingTime(processing_status)
    self._output_writer.Write(f'Processing time: {processing_time:s}\n')

    self._output_writer.Write((
        f'{processing_status.foreman_status.identifier:s} (PID: '
        f'{processing_status.foreman_status.pid:d}) status: '
        f'{processing_status.foreman_status.status:s}, event data produced: '
        f'{processing_status.foreman_status.number_of_produced_event_data:d}, '
        f'events produced: '
        f'{processing_status.foreman_status.number_of_produced_events:d}, '
        f'file: {processing_status.foreman_status.display_name:s}\n'))

    for worker_status in processing_status.workers_status:
      self._output_writer.Write((
          f'{worker_status.identifier:s} (PID: {worker_status.pid:d}) status: '
          f'{worker_status.status:s}, event data produced: '
          f'{worker_status.number_of_produced_events:d}, file: '
          f'{worker_status.display_name:s}\n'))

    self._output_writer.Write('\n')

  def _PrintExtractionStatusUpdateWindow(self, processing_status):
    """Prints an extraction status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    workers_status = processing_status.workers_status

    show_events = bool(
        processing_status.foreman_status.number_of_produced_events and
        not workers_status)

    self._output_writer.Write(
        f'plaso - {self._tool_name:s} version {plaso.__version__:s}\n\n')

    self.PrintExtractionStatusHeader(processing_status)

    if show_events:
      column_name = [
          'Identifier', 'PID', 'Status', 'Memory', 'Sources', 'Events', 'File']
    else:
      column_name = [
          'Identifier', 'PID', 'Status', 'Memory', 'Sources', 'Event Data',
          'File']

    table_view = views.CLITabularTableView(
        column_names=column_name, column_sizes=[15, 7, 15, 15, 15, 15, 0])

    self._AddExtractionProcessStatusTableRow(
        processing_status.foreman_status, table_view, show_events)

    for worker_status in workers_status:
      self._AddExtractionProcessStatusTableRow(
          worker_status, table_view, show_events)

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
    if self._mode == self.MODE_FILE:
      return self._PrintAnalysisStatusUpdateFile

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
    if self._mode == self.MODE_FILE:
      return self._PrintExtractionStatusUpdateFile

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
    self._output_writer.Write(f'Source path\t\t: {self._source_path:s}\n')
    self._output_writer.Write(f'Source type\t\t: {self._source_type:s}\n')

    if self._artifact_filters:
      artifacts_string = ', '.join(self._artifact_filters)
      self._output_writer.Write(f'Artifact filters\t: {artifacts_string:s}\n')
    if self._filter_file:
      self._output_writer.Write(f'Filter file\t\t: {self._filter_file:s}\n')

    processing_time = self._FormatProcessingTime(processing_status)
    self._output_writer.Write(f'Processing time\t\t: {processing_time:s}\n')

    self._PrintTasksStatus(processing_status)
    self._output_writer.Write('\n')

  def PrintExtractionSummary(
      self, processing_status, number_of_extraction_warnings):
    """Prints a summary of the extraction.

    Args:
      processing_status (ProcessingStatus): processing status.
      number_of_extraction_warnings (int): number of extraction warnings.
    """
    if not processing_status:
      self._output_writer.Write(
          'WARNING: missing processing status information.\n')

    elif not processing_status.aborted:
      if processing_status.error_path_specs:
        self._output_writer.Write('Processing completed with errors.\n')
      else:
        self._output_writer.Write('Processing completed.\n')

      if number_of_extraction_warnings:
        output_text = '\n'.join([
            '',
            (f'Number of warnings generated while extracting events: '
             f'{number_of_extraction_warnings:d}.'),
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
          path_spec_string = self._GetPathSpecificationString(path_spec)
          self._output_writer.Write(path_spec_string)
          self._output_writer.Write('\n')

    self._output_writer.Write('\n')

  def SetMode(self, mode):
    """Sets the mode.

    Args:
      mode (str): status view mode.
    """
    self._mode = mode

  def SetStatusFile(self, path):
    """Sets the status file.

    Args:
      path (str): path of the status file.
    """
    self._status_file = path

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
