#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import argparse
import collections
import logging
import os
import sys
import uuid

from plaso.cli import analysis_tool
from plaso.cli import views as cli_views
from plaso.engine import knowledge_base
from plaso.frontend import analysis_frontend
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.storage import zip_file as storage_zip_file


class PinfoTool(analysis_tool.AnalysisTool):
  """Class that implements the pinfo CLI tool."""

  NAME = u'pinfo'
  DESCRIPTION = (
      u'Shows information about a Plaso storage file, for example how it was '
      u'collected, what information was extracted from a source, etc.')

  _INDENTATION_LEVEL = 8

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(PinfoTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._compare_storage_file_path = None

    self._front_end = analysis_frontend.AnalysisFrontend()

    self._verbose = False
    self.compare_storage_information = False

  def _CompareStorages(self, storage, compare_storage):
    """Compares the contents of two storages.

    Args:
      storage (BaseStorage): storage.
      compare_storage (BaseStorage): storage to compare against.

    Returns:
      bool: True if the content of the storages is identical.
    """
    storage_counters = self._CalculateStorageCounters(storage)
    compare_storage_counters = self._CalculateStorageCounters(compare_storage)

    # TODO: improve comparision, currently only total numbers are compared.

    return storage_counters == compare_storage_counters

  def _PrintAnalysisReportCounter(
      self, analysis_reports_counter, session_identifier=None):
    """Prints the analysis reports counter.

    Args:
      analysis_reports_counter (collections.Counter): number of analysis
          reports per analysis plugin.
      session_identifier (Optional[str]): session identifier.
    """
    if not analysis_reports_counter:
      return

    title = u'Reports generated per plugin'
    if session_identifier:
      title = u'{0:s}: {1:s}'.format(title, session_identifier)

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=[u'Plugin name', u'Number of reports'], title=title)

    for key, value in sorted(analysis_reports_counter.items()):
      if key == u'total':
        continue
      table_view.AddRow([key, value])

    try:
      total = analysis_reports_counter[u'total']
    except KeyError:
      total = u'N/A'

    table_view.AddRow([u'Total', total])

    table_view.Write(self._output_writer)

  def _PrintAnalysisReportsDetails(self, storage):
    """Prints the details of the analysis reports.

    Args:
      storage (BaseStorage): storage.
    """
    if not storage.HasAnalysisReports():
      self._output_writer.Write(u'No analysis reports stored.\n\n')
      return

    for index, analysis_report in enumerate(storage.GetAnalysisReports()):
      title = u'Analysis report: {0:d}'.format(index)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def _PrintErrorsDetails(self, storage):
    """Prints the details of the errors.

    Args:
      storage (BaseStorage): storage.
    """
    if not storage.HasErrors():
      self._output_writer.Write(u'No errors stored.\n\n')
      return

    for index, error in enumerate(storage.GetErrors()):
      title = u'Error: {0:d}'.format(index)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'Message', error.message])
      table_view.AddRow([u'Parser chain', error.parser_chain])
      for index, line in enumerate(error.path_spec.comparable.split(u'\n')):
        if not line:
          continue

        if index == 0:
          table_view.AddRow([u'Path specification', line])
        else:
          table_view.AddRow([u'', line])

      table_view.Write(self._output_writer)

  def _PrintEventLabelsCounter(
      self, event_labels_counter, session_identifier=None):
    """Prints the event labels counter.

    Args:
      event_labels_counter (collections.Counter): number of event tags per
          label.
      session_identifier (Optional[str]): session identifier.
    """
    if not event_labels_counter:
      return

    title = u'Event tags generated per label'
    if session_identifier:
      title = u'{0:s}: {1:s}'.format(title, session_identifier)

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=[u'Label', u'Number of event tags'], title=title)

    for key, value in sorted(event_labels_counter.items()):
      if key == u'total':
        continue
      table_view.AddRow([key, value])

    try:
      total = event_labels_counter[u'total']
    except KeyError:
      total = u'N/A'

    table_view.AddRow([u'Total', total])

    table_view.Write(self._output_writer)

  def _PrintParsersCounter(self, parsers_counter, session_identifier=None):
    """Prints the parsers counter

    Args:
      parsers_counter (collections.Counter): number of events per parser or
          parser plugin.
      session_identifier (Optional[str]): session identifier.
    """
    if not parsers_counter:
      return

    title = u'Events generated per parser'
    if session_identifier:
      title = u'{0:s}: {1:s}'.format(title, session_identifier)

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=[u'Parser (plugin) name', u'Number of events'],
        title=title)

    for key, value in sorted(parsers_counter.items()):
      if key == u'total':
        continue
      table_view.AddRow([key, value])

    table_view.AddRow([u'Total', parsers_counter[u'total']])

    table_view.Write(self._output_writer)

  def _PrintPreprocessingInformation(self, storage, session_number=None):
    """Prints the details of the preprocessing information.

    Args:
      storage (BaseStorage): storage.
      session_number (Optional[int]): session number.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()

    storage.ReadPreprocessingInformation(knowledge_base_object)

    system_configuration = knowledge_base_object.GetSystemConfigurationArtifact(
        session_number)
    if not system_configuration:
      return

    title = u'System configuration'
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=title)

    hostname = u'N/A'
    if system_configuration.hostname:
      hostname = system_configuration.hostname.name

    operating_system = system_configuration.operating_system or u'N/A'
    operating_system_product = (
        system_configuration.operating_system_product or u'N/A')
    operating_system_version = (
        system_configuration.operating_system_version or u'N/A')
    code_page = system_configuration.code_page or u'N/A'
    keyboard_layout = system_configuration.keyboard_layout or u'N/A'
    time_zone = system_configuration.time_zone or u'N/A'

    table_view.AddRow([u'Hostname', hostname])
    table_view.AddRow([u'Operating system', operating_system])
    table_view.AddRow([u'Operating system product', operating_system_product])
    table_view.AddRow([u'Operating system version', operating_system_version])
    table_view.AddRow([u'Code page', code_page])
    table_view.AddRow([u'Keyboard layout', keyboard_layout])
    table_view.AddRow([u'Time zone', time_zone])

    table_view.Write(self._output_writer)

    title = u'User accounts'
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=title)

    for user_account in system_configuration.user_accounts:
      table_view.AddRow([
          user_account.username, user_account.user_directory])

    table_view.Write(self._output_writer)

  def _PrintSessionsDetails(self, storage):
    """Prints the details of the sessions.

    Args:
      storage (BaseStorage): storage.
    """
    for session_number, session in enumerate(storage.GetSessions()):
      session_identifier = uuid.UUID(hex=session.identifier)

      start_time = u'N/A'
      if session.start_time is not None:
        start_time = timelib.Timestamp.CopyToIsoFormat(session.start_time)

      completion_time = u'N/A'
      if session.completion_time is not None:
        completion_time = timelib.Timestamp.CopyToIsoFormat(
            session.completion_time)

      enabled_parser_names = u'N/A'
      if session.enabled_parser_names:
        enabled_parser_names = u', '.join(sorted(session.enabled_parser_names))

      command_line_arguments = session.command_line_arguments or u'N/A'
      parser_filter_expression = session.parser_filter_expression or u'N/A'
      preferred_encoding = session.preferred_encoding or u'N/A'
      filter_file = session.filter_file or u'N/A'
      filter_expression = session.filter_expression or u'N/A'

      title = u'Session: {0!s}'.format(session_identifier)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'Start time', start_time])
      table_view.AddRow([u'Completion time', completion_time])
      table_view.AddRow([u'Product name', session.product_name])
      table_view.AddRow([u'Product version', session.product_version])
      table_view.AddRow([u'Command line arguments', command_line_arguments])
      table_view.AddRow([u'Parser filter expression', parser_filter_expression])
      table_view.AddRow([u'Enabled parser and plugins', enabled_parser_names])
      table_view.AddRow([u'Preferred encoding', preferred_encoding])
      table_view.AddRow([u'Debug mode', session.debug_mode])
      table_view.AddRow([u'Filter file', filter_file])
      table_view.AddRow([u'Filter expression', filter_expression])

      table_view.Write(self._output_writer)

      if self._verbose:
        self._PrintPreprocessingInformation(storage, session_number + 1)

        self._PrintParsersCounter(
            session.parsers_counter, session_identifier=session_identifier)

        self._PrintAnalysisReportCounter(
            session.analysis_reports_counter,
            session_identifier=session_identifier)

        self._PrintEventLabelsCounter(
            session.event_labels_counter,
            session_identifier=session_identifier)

  def _PrintSessionsOverview(self, storage):
    """Prints a sessions overview.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Sessions')

    for session in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          session.start_time)
      session_identifier = uuid.UUID(hex=session.identifier)
      table_view.AddRow([str(session_identifier), start_time])

    table_view.Write(self._output_writer)

  def _CalculateStorageCounters(self, storage):
    """Calculates the counters of the entire storage.

    Args:
      storage (BaseStorage): storage.

    Returns:
      dict[str,collections.Counter]: storage counters.
    """
    analysis_reports_counter = collections.Counter()
    analysis_reports_counter_error = False
    event_labels_counter = collections.Counter()
    event_labels_counter_error = False
    parsers_counter = collections.Counter()
    parsers_counter_error = False

    for session in storage.GetSessions():
      # Check for a dict for backwards compatibility.
      if isinstance(session.analysis_reports_counter, dict):
        analysis_reports_counter += collections.Counter(
            session.analysis_reports_counter)
      elif isinstance(session.analysis_reports_counter, collections.Counter):
        analysis_reports_counter += session.analysis_reports_counter
      else:
        analysis_reports_counter_error = True

      # Check for a dict for backwards compatibility.
      if isinstance(session.event_labels_counter, dict):
        event_labels_counter += collections.Counter(
            session.event_labels_counter)
      elif isinstance(session.event_labels_counter, collections.Counter):
        event_labels_counter += session.event_labels_counter
      else:
        event_labels_counter_error = True

      # Check for a dict for backwards compatibility.
      if isinstance(session.parsers_counter, dict):
        parsers_counter += collections.Counter(session.parsers_counter)
      elif isinstance(session.parsers_counter, collections.Counter):
        parsers_counter += session.parsers_counter
      else:
        parsers_counter_error = True

    storage_counters = {}

    if not analysis_reports_counter_error:
      storage_counters[u'analysis_reports'] = analysis_reports_counter

    if not event_labels_counter_error:
      storage_counters[u'event_labels'] = event_labels_counter

    if not parsers_counter_error:
      storage_counters[u'parsers'] = parsers_counter

    return storage_counters

  def _PrintStorageInformation(self, storage):
    """Prints information about the storage.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Plaso Storage Information')
    table_view.AddRow([u'Filename', os.path.basename(self._storage_file_path)])
    table_view.AddRow([u'Format version', storage.format_version])
    table_view.AddRow([u'Serialization format', storage.serialization_format])
    table_view.Write(self._output_writer)

    if storage.storage_type == definitions.STORAGE_TYPE_SESSION:
      self._PrintSessionsOverview(storage)
      self._PrintSessionsDetails(storage)

      storage_counters = self._CalculateStorageCounters(storage)

      if u'parsers' not in storage_counters:
        self._output_writer.Write(
            u'Unable to determine number of events generated per parser.\n')
      else:
        self._PrintParsersCounter(storage_counters[u'parsers'])

      if u'analysis_reports' not in storage_counters:
        self._output_writer.Write(
            u'Unable to determine number of reports generated per plugin.\n')
      else:
        self._PrintAnalysisReportCounter(storage_counters[u'analysis_reports'])

      if u'event_labels' not in storage_counters:
        self._output_writer.Write(
            u'Unable to determine number of event tags generated per label.\n')
      else:
        self._PrintEventLabelsCounter(storage_counters[u'event_labels'])

      self._PrintErrorsDetails(storage)
      self._PrintAnalysisReportsDetails(storage)

    elif storage.storage_type == definitions.STORAGE_TYPE_TASK:
      self._PrintTasksInformation(storage)

    return

  def _PrintTasksInformation(self, storage):
    """Prints information about the tasks.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Tasks')

    for task_start, _ in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          task_start.timestamp)
      task_identifier = uuid.UUID(hex=task_start.identifier)
      table_view.AddRow([str(task_identifier), start_time])

    table_view.Write(self._output_writer)

  def CompareStorages(self):
    """Compares the contents of two storages.

    Returns:
      bool: True if the content of the storages is identical.
    """
    storage_file = storage_zip_file.ZIPStorageFile()
    try:
      storage_file.Open(path=self._storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    compare_storage_file = storage_zip_file.ZIPStorageFile()
    try:
      compare_storage_file.Open(
          path=self._compare_storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._compare_storage_file_path, exception))
      storage_file.Close()
      return

    try:
      result = self._CompareStorages(storage_file, compare_storage_file)

    finally:
      compare_storage_file.Close()
      storage_file.Close()

    if result:
      self._output_writer.Write(u'Storages are identical.\n')
    else:
      self._output_writer.Write(u'Storages are different.\n')

    return result

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddStorageFileOptions(argument_parser)

    argument_parser.add_argument(
        u'-v', u'--verbose', dest=u'verbose', action=u'store_true',
        default=False, help=u'Print verbose output.')

    argument_parser.add_argument(
        u'--compare', dest=u'compare_storage_file', type=str,
        action=u'store', default=u'', metavar=u'STORAGE_FILE', help=(
            u'The path of the storage file to compare against.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PinfoTool, self).ParseOptions(options)

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self._ConfigureLogging(log_level=logging_level)

    self._verbose = getattr(options, u'verbose', False)

    compare_storage_file_path = self.ParseStringOption(
        options, u'compare_storage_file')
    if compare_storage_file_path:
      if not os.path.isfile(compare_storage_file_path):
        raise errors.BadConfigOption(
            u'No such storage file: {0:s}.'.format(compare_storage_file_path))

      self._compare_storage_file_path = compare_storage_file_path
      self.compare_storage_information = True

  def PrintStorageInformation(self):
    """Prints the storage information."""
    storage_file = storage_zip_file.ZIPStorageFile()
    try:
      storage_file.Open(path=self._storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    try:
      self._PrintStorageInformation(storage_file)
    finally:
      storage_file.Close()


def Main():
  """The main function."""
  tool = PinfoTool()

  if not tool.ParseArguments():
    return False

  result = True
  if tool.compare_storage_information:
    result = tool.CompareStorages()
  else:
    tool.PrintStorageInformation()
  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
