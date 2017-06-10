# -*- coding: utf-8 -*-
"""The status view."""

import sys

try:
  import win32console
except ImportError:
  win32console = None

from dfvfs.lib import definitions as dfvfs_definitions

import plaso

from plaso.lib import definitions
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views


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
        output_writer, cli_tools.StdoutOutputWriter)
    self._tool_name = tool_name

  def _FormatExtractionStatusTableRow(self, process_status):
    """Formats an extraction status table row.

    Args:
      process_status (ProcessStatus): processing status.
    """
    # This check makes sure the columns are tab aligned.
    identifier = process_status.identifier
    if len(identifier) < 8:
      identifier = u'{0:s}\t'.format(identifier)

    status = process_status.status
    if len(status) < 8:
      status = u'{0:s}\t'.format(status)

    sources = u''
    if (process_status.number_of_produced_sources is not None and
        process_status.number_of_produced_sources_delta is not None):
      sources = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_sources,
          process_status.number_of_produced_sources_delta)

    # This check makes sure the columns are tab aligned.
    if len(sources) < 8:
      sources = u'{0:s}\t'.format(sources)

    events = u''
    if (process_status.number_of_produced_events is not None and
        process_status.number_of_produced_events_delta is not None):
      events = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_events,
          process_status.number_of_produced_events_delta)

    # This check makes sure the columns are tab aligned.
    if len(events) < 8:
      events = u'{0:s}\t'.format(events)

    used_memory = self._FormatSizeInUnitsOf1024(process_status.used_memory)
    if len(used_memory) < 8:
      used_memory = u'{0:s}\t'.format(used_memory)

    # TODO: shorten display name to fit in 80 chars and show the filename.
    return u'{0:s}\t{1:d}\t{2:s}\t{3:s}\t{4:s}\t{5:s}\t{6:s}'.format(
        identifier, process_status.pid, status, used_memory, sources, events,
        process_status.display_name)

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

    self.PrintExtractionStatusHeader()

    # TODO: for win32console get current color and set intensity,
    # write the header separately then reset intensity.
    status_header = (
        u'Identifier\tPID\tStatus\t\tMemory\t\tSources\t\tEvents\t\tFile')
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

  def GetExtractionStatusUpdateCallback(self):
    """Retrieves the extraction status update callback function.

    Returns:
      function: status update callback function or None.
    """
    if self._mode == self.MODE_LINEAR:
      return self._PrintExtractionStatusUpdateLinear
    elif self._mode == self.MODE_WINDOW:
      return self._PrintExtractionStatusUpdateWindow

  def PrintAnalysisReportsDetails(self, storage, number_of_analysis_reports):
    """Prints the details of the analysis reports.

    Args:
      storage (BaseStorage): storage writer.
      number_of_analysis_reports (int): number of analysis reports.
    """
    for index, analysis_report in enumerate(storage.GetAnalysisReports()):
      if index + 1 <= number_of_analysis_reports:
        continue

      title = u'Analysis report: {0:d}'.format(index)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  # TODO: refactor to protected method.
  def PrintExtractionStatusHeader(self):
    """Prints the extraction status header."""
    self._output_writer.Write(
        u'Source path\t: {0:s}\n'.format(self._source_path))
    self._output_writer.Write(
        u'Source type\t: {0:s}\n'.format(self._source_type))

    if self._filter_file:
      self._output_writer.Write(u'Filter file\t: {0:s}\n'.format(
          self._filter_file))

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
