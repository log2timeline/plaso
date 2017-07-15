# -*- coding: utf-8 -*-
"""The status view."""

import sys

try:
  import win32api
  import win32console
except ImportError:
  win32console = None

from dfvfs.lib import definitions as dfvfs_definitions

import plaso

from plaso.lib import definitions
from plaso.cli import tools


class StatusView(object):
  """Processing status view."""

  MODE_LINEAR = u'linear'
  MODE_WINDOW = u'window'

  _SOURCE_TYPES = {
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY: u'directory',
      dfvfs_definitions.SOURCE_TYPE_FILE: u'single file',
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE: (
          u'storage media device'),
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE: (
          u'storage media image')}

  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

  def __init__(self, output_writer, tool_name):
    """Initializes a status view.

    Args:
      output_writer (OutputWriter): output writer.
      tool_name (str): namd of the tool.
    """
    super(StatusView, self).__init__()
    self._filter_file = None
    self._mode = self.MODE_WINDOW
    self._output_writer = output_writer
    self._source_path = None
    self._source_type = None
    self._stdout_output_writer = isinstance(
        output_writer, tools.StdoutOutputWriter)
    self._storage_file_path = None
    self._tool_name = tool_name

  def _ClearScreen(self):
    """Clears the terminal/console screen."""
    if not win32console:
      # ANSI escape sequence to clear screen.
      self._output_writer.Write(b'\033[2J')
      # ANSI escape sequence to move cursor to top left.
      self._output_writer.Write(b'\033[H')

    else:
      # Windows cmd.exe does not support ANSI escape codes, thus instead we
      # fill the console screen buffer with spaces.
      top_left_coordinate = win32console.PyCOORDType(0, 0)
      screen_buffer = win32console.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
      screen_buffer_information = screen_buffer.GetConsoleScreenBufferInfo()

      screen_buffer_attributes = screen_buffer_information[u'Attributes']
      screen_buffer_size = screen_buffer_information[u'Size']
      console_size = screen_buffer_size.X * screen_buffer_size.Y

      screen_buffer.FillConsoleOutputCharacter(
          u' ', console_size, top_left_coordinate)
      screen_buffer.FillConsoleOutputAttribute(
          screen_buffer_attributes, console_size, top_left_coordinate)
      screen_buffer.SetConsoleCursorPosition(top_left_coordinate)

  def _FormatAnalysisStatusTableRow(self, process_status):
    """Formats an analysis status table row.

    Args:
      process_status (ProcessStatus): processing status.

    Returns:
      str: processing status formatted as a row.
    """
    pid = u'{0:d}'.format(process_status.pid)

    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)

    events = u''
    if (process_status.number_of_consumed_events is not None and
        process_status.number_of_consumed_events_delta is not None):
      events = u'{0:d} ({1:d})'.format(
          process_status.number_of_consumed_events,
          process_status.number_of_consumed_events_delta)

    event_tags = u''
    if (process_status.number_of_produced_event_tags is not None and
        process_status.number_of_produced_event_tags_delta is not None):
      event_tags = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_event_tags,
          process_status.number_of_produced_event_tags_delta)

    reports = u''
    if (process_status.number_of_produced_reports is not None and
        process_status.number_of_produced_reports_delta is not None):
      reports = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_reports,
          process_status.number_of_produced_reports_delta)

    # The columns are 8-spaces aligned.
    return u''.join([
        process_status.identifier,
        u' ' * (24 - len(process_status.identifier)),
        pid,
        u' ' * (8 - len(pid)),
        process_status.status,
        u' ' * (16 - len(process_status.status)),
        used_memory,
        u' ' * (16 - len(used_memory)),
        events,
        u' ' * (16 - len(events)),
        event_tags,
        u' ' * (16 - len(event_tags)),
        reports])

  def _FormatExtractionStatusTableRow(self, process_status):
    """Formats an extraction status table row.

    Args:
      process_status (ProcessStatus): processing status.

    Returns:
      str: processing status formatted as a row.
    """
    pid = u'{0:d}'.format(process_status.pid)

    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)

    sources = u''
    if (process_status.number_of_produced_sources is not None and
        process_status.number_of_produced_sources_delta is not None):
      sources = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_sources,
          process_status.number_of_produced_sources_delta)

    events = u''
    if (process_status.number_of_produced_events is not None and
        process_status.number_of_produced_events_delta is not None):
      events = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_events,
          process_status.number_of_produced_events_delta)

    # TODO: shorten display name to fit in 80 chars and show the filename.

    # The columns are 8-spaces aligned.
    return u''.join([
        process_status.identifier,
        u' ' * (16 - len(process_status.identifier)),
        pid,
        u' ' * (8 - len(pid)),
        process_status.status,
        u' ' * (16 - len(process_status.status)),
        used_memory,
        u' ' * (16 - len(used_memory)),
        sources,
        u' ' * (16 - len(sources)),
        events,
        u' ' * (16 - len(events)),
        process_status.display_name])

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

    if magnitude_1024 > 0 and magnitude_1024 <= 7:
      return u'{0:.1f} {1:s}'.format(
          used_memory_1024, self._UNITS_1024[magnitude_1024])

    return u'{0:d} B'.format(size)

  def _PrintAnalysisStatusHeader(self):
    """Prints the analysis status header."""
    self._output_writer.Write(
        u'Storage file\t: {0:s}\n'.format(self._storage_file_path))

    self._output_writer.Write(u'\n')

  def _PrintAnalysisStatusUpdateLinear(self, processing_status):
    """Prints an analysis status update in linear mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    for worker_status in processing_status.workers_status:
      status_line = (
          u'{0:s} (PID: {1:d}) - events consumed: {2:d} - running: '
          u'{3!s}\n').format(
              worker_status.identifier, worker_status.pid,
              worker_status.number_of_consumed_events,
              worker_status.status not in definitions.PROCESSING_ERROR_STATUS)
      self._output_writer.Write(status_line)

  def _PrintAnalysisStatusUpdateWindow(self, processing_status):
    """Prints an analysis status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    output_text = u'plaso - {0:s} version {1:s}\n\n'.format(
        self._tool_name, plaso.__version__)
    self._output_writer.Write(output_text)

    self._PrintAnalysisStatusHeader()

    status_header = (
        u'Identifier              '
        u'PID     '
        u'Status          '
        u'Memory          '
        u'Events          '
        u'Tags            '
        u'Reports')
    if not win32console:
      # TODO: for win32console get current color and set intensity,
      # write the header separately then reset intensity.
      status_header = u'\x1b[1m{0:s}\x1b[0m'.format(status_header)

    status_table = [status_header]

    status_row = self._FormatAnalysisStatusTableRow(
        processing_status.foreman_status)
    status_table.append(status_row)

    for worker_status in processing_status.workers_status:
      status_row = self._FormatAnalysisStatusTableRow(worker_status)
      status_table.append(status_row)

    status_table.append(u'')
    self._output_writer.Write(u'\n'.join(status_table))
    self._output_writer.Write(u'\n')

    if processing_status.aborted:
      self._output_writer.Write(
          u'Processing aborted - waiting for clean up.\n\n')

    # TODO: remove update flicker. For win32console we could set the cursor
    # top left, write the table, clean the remainder of the screen buffer
    # and set the cursor at the end of the table.
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
          u'{0:s} (PID: {1:d}) - events produced: {2:d} - file: {3:s} '
          u'- running: {4!s}\n').format(
              worker_status.identifier, worker_status.pid,
              worker_status.number_of_produced_events,
              worker_status.display_name,
              worker_status.status not in definitions.PROCESSING_ERROR_STATUS)
      self._output_writer.Write(status_line)

  def _PrintExtractionStatusUpdateWindow(self, processing_status):
    """Prints an extraction status update in window mode.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    output_text = u'plaso - {0:s} version {1:s}\n\n'.format(
        self._tool_name, plaso.__version__)
    self._output_writer.Write(output_text)

    self.PrintExtractionStatusHeader(processing_status)

    # TODO: for win32console get current color and set intensity,
    # write the header separately then reset intensity.
    status_header = (
        u'Identifier      '
        u'PID     '
        u'Status          '
        u'Memory          '
        u'Sources         '
        u'Events          '
        u'File')
    if not win32console:
      status_header = u'\x1b[1m{0:s}\x1b[0m'.format(status_header)

    status_table = [status_header]

    status_row = self._FormatExtractionStatusTableRow(
        processing_status.foreman_status)
    status_table.append(status_row)

    for worker_status in processing_status.workers_status:
      status_row = self._FormatExtractionStatusTableRow(worker_status)
      status_table.append(status_row)

    status_table.append(u'')
    self._output_writer.Write(u'\n'.join(status_table))
    self._output_writer.Write(u'\n')

    if processing_status.aborted:
      self._output_writer.Write(
          u'Processing aborted - waiting for clean up.\n\n')

    # TODO: remove update flicker. For win32console we could set the cursor
    # top left, write the table, clean the remainder of the screen buffer
    # and set the cursor at the end of the table.
    if self._stdout_output_writer:
      # We need to explicitly flush stdout to prevent partial status updates.
      sys.stdout.flush()

  def GetAnalysisStatusUpdateCallback(self):
    """Retrieves the analysis status update callback function.

    Returns:
      function: status update callback function or None.
    """
    if self._mode == self.MODE_LINEAR:
      return self._PrintAnalysisStatusUpdateLinear
    elif self._mode == self.MODE_WINDOW:
      return self._PrintAnalysisStatusUpdateWindow

  def GetExtractionStatusUpdateCallback(self):
    """Retrieves the extraction status update callback function.

    Returns:
      function: status update callback function or None.
    """
    if self._mode == self.MODE_LINEAR:
      return self._PrintExtractionStatusUpdateLinear
    elif self._mode == self.MODE_WINDOW:
      return self._PrintExtractionStatusUpdateWindow

  # TODO: refactor to protected method.
  def PrintExtractionStatusHeader(self, processing_status):
    """Prints the extraction status header.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    self._output_writer.Write(
        u'Source path\t: {0:s}\n'.format(self._source_path))
    self._output_writer.Write(
        u'Source type\t: {0:s}\n'.format(self._source_type))

    if self._filter_file:
      self._output_writer.Write(u'Filter file\t: {0:s}\n'.format(
          self._filter_file))

    if processing_status and processing_status.tasks_status:
      tasks_status = processing_status.tasks_status

      self._output_writer.Write(u'\n')

      status_header = (
          u'Tasks:          '
          u'Queued  '
          u'Processing      '
          u'To merge        '
          u'Abandoned       '
          u'Total')

      if not win32console:
        status_header = u'\x1b[1m{0:s}\x1b[0m\n'.format(status_header)
      else:
        status_header = u'{0:s}\n'.format(status_header)

      self._output_writer.Write(status_header)

      number_of_queued_tasks = u'{0:d}'.format(
          tasks_status.number_of_queued_tasks)
      number_of_tasks_processing = u'{0:d}'.format(
          tasks_status.number_of_tasks_processing)
      number_of_tasks_pending_merge = u'{0:d}'.format(
          tasks_status.number_of_tasks_pending_merge)
      number_of_abandoned_tasks = u'{0:d}'.format(
          tasks_status.number_of_abandoned_tasks)
      total_number_of_tasks = u'{0:d}'.format(
          tasks_status.total_number_of_tasks)

      # The columns are 8-spaces aligned.
      status_line = u''.join([
          u' ' * 16,
          number_of_queued_tasks,
          u' ' * (8 - len(number_of_queued_tasks)),
          number_of_tasks_processing,
          u' ' * (16 - len(number_of_tasks_processing)),
          number_of_tasks_pending_merge,
          u' ' * (16 - len(number_of_tasks_pending_merge)),
          number_of_abandoned_tasks,
          u' ' * (16 - len(number_of_abandoned_tasks)),
          total_number_of_tasks])

      self._output_writer.Write(status_line)
      self._output_writer.Write(u'\n')

    self._output_writer.Write(u'\n')

  def PrintExtractionSummary(self, processing_status):
    """Prints a summary of the extraction.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if not processing_status:
      self._output_writer.Write(
          u'WARNING: missing processing status information.\n')

    elif not processing_status.aborted:
      if processing_status.error_path_specs:
        self._output_writer.Write(u'Processing completed with errors.\n')
      else:
        self._output_writer.Write(u'Processing completed.\n')

      number_of_errors = (
          processing_status.foreman_status.number_of_produced_errors)
      if number_of_errors:
        output_text = u'\n'.join([
            u'',
            (u'Number of errors encountered while extracting events: '
             u'{0:d}.').format(number_of_errors),
            u'',
            u'Use pinfo to inspect errors in more detail.',
            u''])
        self._output_writer.Write(output_text)

      if processing_status.error_path_specs:
        output_text = u'\n'.join([
            u'',
            u'Path specifications that could not be processed:',
            u''])
        self._output_writer.Write(output_text)
        for path_spec in processing_status.error_path_specs:
          self._output_writer.Write(path_spec.comparable)
          self._output_writer.Write(u'\n')

    self._output_writer.Write(u'\n')

  def SetMode(self, mode):
    """Sets the mode.

    Args:
      mode (str): status view mode.
    """
    self._mode = mode

  def SetSourceInformation(self, source_path, source_type, filter_file=None):
    """Sets the source information.

    Args:
      source_path (str): path of the source.
      source_type (str): source type.
      filter_file (Optional[str]): filter file.
    """
    self._filter_file = filter_file
    self._source_path = source_path
    self._source_type = self._SOURCE_TYPES.get(source_type, u'UNKNOWN')

  def SetStorageFileInformation(self, storage_file_path):
    """Sets the storage file information.

    Args:
      storage_file_path (str): path to the storage file.
    """
    self._storage_file_path = storage_file_path
