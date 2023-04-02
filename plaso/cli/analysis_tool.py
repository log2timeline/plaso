# -*- coding: utf-8 -*-
"""Shared functionality for an analysis CLI tool."""

import time

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.analysis import manager as analysis_manager
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.containers import reports
from plaso.multi_process import analysis_engine as multi_analysis_engine
from plaso.storage import factory as storage_factory


class AnalysisTool(
    tools.CLITool,
    tool_options.AnalysisPluginOptions,
    tool_options.ProfilingOptions,
    tool_options.StorageFileOptions):
  """Analysis CLI tool.

  Attributes:
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
  """

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(AnalysisTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_manager = analysis_manager.AnalysisPluginManager
    self._analysis_plugins = None
    self._analysis_plugins_output_format = None
    self._command_line_arguments = None
    self._event_filter_expression = None
    self._event_filter = None
    self._number_of_stored_analysis_reports = 0
    self._status_view_interval = 0.5
    self._storage_file_path = None
    self._worker_memory_limit = None
    self._worker_timeout = None

    self.list_analysis_plugins = False

  def _AnalyzeEvents(self, session, configuration, status_update_callback=None):
    """Analyzes events in a Plaso storage.

    Args:
      session (Session): session in which the events are analyzed.
      configuration (ProcessingConfiguration): processing configuration.
      status_update_callback (Optional[function]): callback function for status
          updates.

    Returns:
      ProcessingStatus: processing status.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    storage_writer = storage_factory.StorageFactory.CreateStorageWriterForFile(
        self._storage_file_path)
    if not storage_writer:
      raise RuntimeError('Unable to create storage writer.')

    # TODO: add single process analysis engine support.
    analysis_engine = multi_analysis_engine.AnalysisMultiProcessEngine(
        worker_memory_limit=self._worker_memory_limit,
        worker_timeout=self._worker_timeout)

    analysis_engine.SetStatusUpdateInterval(self._status_view_interval)

    storage_writer.Open(path=self._storage_file_path)

    processing_status = None

    session.command_line_arguments = self._command_line_arguments
    session.debug_mode = self._debug_mode

    try:
      storage_writer.AddAttributeContainer(session)

      try:
        processing_status = analysis_engine.AnalyzeEvents(
            session, storage_writer, self._data_location,
            self._analysis_plugins, configuration,
            event_filter=self._event_filter,
            event_filter_expression=self._event_filter_expression,
            status_update_callback=status_update_callback,
            storage_file_path=self._storage_file_path)

      finally:
        session.aborted = getattr(processing_status, 'aborted', True)
        session.completion_time = int(time.time() * 1000000)
        storage_writer.UpdateAttributeContainer(session)

    finally:
      storage_writer.Close()

    return processing_status

  def _PrintAnalysisReportsDetails(self, storage_reader):
    """Prints the details of the analysis reports.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    generator = storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

    for index, analysis_report in enumerate(generator):
      if index + 1 <= self._number_of_stored_analysis_reports:
        continue

      date_time_string = None
      if analysis_report.time_compiled is not None:
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=analysis_report.time_compiled)
        date_time_string = date_time.CopyToDateTimeStringISO8601()

      title = 'Analysis report: {0:s}'.format(analysis_report.plugin_name)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Date and time', date_time_string or 'N/A'])
      table_view.AddRow(['Event filter', analysis_report.event_filter or 'N/A'])

      if not analysis_report.analysis_counter:
        table_view.AddRow(['Text', analysis_report.text or ''])
      else:
        text = 'Results'
        for key, value in sorted(analysis_report.analysis_counter.items()):
          table_view.AddRow([text, '{0:s}: {1:d}'.format(key, value)])
          text = ''

      table_view.Write(self._output_writer)
