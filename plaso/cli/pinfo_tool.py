# -*- coding: utf-8 -*-
"""The pinfo CLI tool."""

from __future__ import unicode_literals

import argparse
import collections
import os
import uuid

from plaso.cli import logger
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.serializer import json_serializer
from plaso.storage import factory as storage_factory


class PinfoTool(
    tools.CLITool,
    tool_options.StorageFileOptions):
  """Pinfo CLI tool."""

  NAME = 'pinfo'
  DESCRIPTION = (
      'Shows information about a Plaso storage file, for example how it was '
      'collected, what information was extracted from a source, etc.')

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
    self._output_filename = None
    self._output_format = None
    self._process_memory_limit = None
    self._storage_file_path = None

    self._verbose = False
    self.compare_storage_information = False

  def _CalculateStorageCounters(self, storage):
    """Calculates the counters of the entire storage.

    Args:
      storage (BaseStore): storage.

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
      storage_counters['analysis_reports'] = analysis_reports_counter

    if not event_labels_counter_error:
      storage_counters['event_labels'] = event_labels_counter

    if not parsers_counter_error:
      storage_counters['parsers'] = parsers_counter

    return storage_counters

  def _CompareStores(self, storage, compare_storage):
    """Compares the contents of two stores.

    Args:
      storage (BaseStore): storage.
      compare_storage (BaseStore): storage to compare against.

    Returns:
      bool: True if the content of the stores is identical.
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

    title = 'Reports generated per plugin'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Plugin name', 'Number of reports'], title=title)

    for key, value in sorted(analysis_reports_counter.items()):
      if key == 'total':
        continue
      table_view.AddRow([key, value])

    try:
      total = analysis_reports_counter['total']
    except KeyError:
      total = 'N/A'

    table_view.AddRow(['Total', total])

    table_view.Write(self._output_writer)

  def _PrintAnalysisReportsDetails(self, storage):
    """Prints the details of the analysis reports.

    Args:
      storage (BaseStore): storage.
    """
    if not storage.HasAnalysisReports():
      self._output_writer.Write('No analysis reports stored.\n\n')
      return

    for index, analysis_report in enumerate(storage.GetAnalysisReports()):
      title = 'Analysis report: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def _PrintErrorsDetails(self, storage):
    """Prints the details of the errors.

    Args:
      storage (BaseStore): storage.
    """
    if not storage.HasErrors():
      self._output_writer.Write('No errors stored.\n\n')
      return

    for index, error in enumerate(storage.GetErrors()):
      title = 'Error: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Message', error.message])
      table_view.AddRow(['Parser chain', error.parser_chain])

      path_specification = error.path_spec.comparable
      for path_index, line in enumerate(path_specification.split('\n')):
        if not line:
          continue

        if path_index == 0:
          table_view.AddRow(['Path specification', line])
        else:
          table_view.AddRow(['', line])

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

    title = 'Event tags generated per label'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Label', 'Number of event tags'], title=title)

    for key, value in sorted(event_labels_counter.items()):
      if key == 'total':
        continue
      table_view.AddRow([key, value])

    try:
      total = event_labels_counter['total']
    except KeyError:
      total = 'N/A'

    table_view.AddRow(['Total', total])

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

    title = 'Events generated per parser'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Parser (plugin) name', 'Number of events'],
        title=title)

    for key, value in sorted(parsers_counter.items()):
      if key == 'total':
        continue
      table_view.AddRow([key, value])

    table_view.AddRow(['Total', parsers_counter['total']])

    table_view.Write(self._output_writer)

  def _PrintPreprocessingInformation(self, storage, session_number=None):
    """Prints the details of the preprocessing information.

    Args:
      storage (BaseStore): storage.
      session_number (Optional[int]): session number.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()

    storage.ReadPreprocessingInformation(knowledge_base_object)

    # TODO: replace session_number by session_identifier.
    system_configuration = knowledge_base_object.GetSystemConfigurationArtifact(
        session_identifier=session_number)
    if not system_configuration:
      return

    title = 'System configuration'
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title=title)

    hostname = 'N/A'
    if system_configuration.hostname:
      hostname = system_configuration.hostname.name

    operating_system = system_configuration.operating_system or 'N/A'
    operating_system_product = (
        system_configuration.operating_system_product or 'N/A')
    operating_system_version = (
        system_configuration.operating_system_version or 'N/A')
    code_page = system_configuration.code_page or 'N/A'
    keyboard_layout = system_configuration.keyboard_layout or 'N/A'
    time_zone = system_configuration.time_zone or 'N/A'

    table_view.AddRow(['Hostname', hostname])
    table_view.AddRow(['Operating system', operating_system])
    table_view.AddRow(['Operating system product', operating_system_product])
    table_view.AddRow(['Operating system version', operating_system_version])
    table_view.AddRow(['Code page', code_page])
    table_view.AddRow(['Keyboard layout', keyboard_layout])
    table_view.AddRow(['Time zone', time_zone])

    table_view.Write(self._output_writer)

    title = 'User accounts'
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Username', 'User directory'], title=title)

    for user_account in system_configuration.user_accounts:
      table_view.AddRow([
          user_account.username, user_account.user_directory])

    table_view.Write(self._output_writer)

  def _PrintSessionsDetails(self, storage):
    """Prints the details of the sessions.

    Args:
      storage (BaseStore): storage.
    """
    for session_number, session in enumerate(storage.GetSessions()):
      session_identifier = uuid.UUID(hex=session.identifier)

      start_time = 'N/A'
      if session.start_time is not None:
        start_time = timelib.Timestamp.CopyToIsoFormat(session.start_time)

      completion_time = 'N/A'
      if session.completion_time is not None:
        completion_time = timelib.Timestamp.CopyToIsoFormat(
            session.completion_time)

      enabled_parser_names = 'N/A'
      if session.enabled_parser_names:
        enabled_parser_names = ', '.join(sorted(session.enabled_parser_names))

      command_line_arguments = session.command_line_arguments or 'N/A'
      parser_filter_expression = session.parser_filter_expression or 'N/A'
      preferred_encoding = session.preferred_encoding or 'N/A'
      # Workaround for some older Plaso releases writing preferred encoding as
      # bytes.
      if isinstance(preferred_encoding, py2to3.BYTES_TYPE):
        preferred_encoding = preferred_encoding.decode('utf-8')
      artifact_filters = session.artifact_filters or 'N/A'
      filter_file = session.filter_file or 'N/A'

      title = 'Session: {0!s}'.format(session_identifier)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Start time', start_time])
      table_view.AddRow(['Completion time', completion_time])
      table_view.AddRow(['Product name', session.product_name])
      table_view.AddRow(['Product version', session.product_version])
      table_view.AddRow(['Command line arguments', command_line_arguments])
      table_view.AddRow(['Parser filter expression', parser_filter_expression])
      table_view.AddRow(['Enabled parser and plugins', enabled_parser_names])
      table_view.AddRow(['Preferred encoding', preferred_encoding])
      table_view.AddRow(['Debug mode', session.debug_mode])
      table_view.AddRow(['Artifact filters', artifact_filters])
      table_view.AddRow(['Filter file', filter_file])

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
      storage (BaseStore): storage.
    """
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Sessions')

    for session in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          session.start_time)
      session_identifier = uuid.UUID(hex=session.identifier)
      table_view.AddRow([str(session_identifier), start_time])

    table_view.Write(self._output_writer)

  def _PrintStorageInformationAsText(self, storage):
    """Prints information about the store as human-readable text.

    Args:
      storage (BaseStore): storage.
    """
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Plaso Storage Information')
    table_view.AddRow(['Filename', os.path.basename(self._storage_file_path)])
    table_view.AddRow(['Format version', storage.format_version])
    table_view.AddRow(['Serialization format', storage.serialization_format])
    table_view.Write(self._output_writer)

    if storage.storage_type == definitions.STORAGE_TYPE_SESSION:
      self._PrintSessionsOverview(storage)
      self._PrintSessionsDetails(storage)

      storage_counters = self._CalculateStorageCounters(storage)

      if 'parsers' not in storage_counters:
        self._output_writer.Write(
            'Unable to determine number of events generated per parser.\n')
      else:
        self._PrintParsersCounter(storage_counters['parsers'])

      if 'analysis_reports' not in storage_counters:
        self._output_writer.Write(
            'Unable to determine number of reports generated per plugin.\n')
      else:
        self._PrintAnalysisReportCounter(storage_counters['analysis_reports'])

      if 'event_labels' not in storage_counters:
        self._output_writer.Write(
            'Unable to determine number of event tags generated per label.\n')
      else:
        self._PrintEventLabelsCounter(storage_counters['event_labels'])

      self._PrintErrorsDetails(storage)
      self._PrintAnalysisReportsDetails(storage)

    elif storage.storage_type == definitions.STORAGE_TYPE_TASK:
      self._PrintTasksInformation(storage)

  def _PrintStorageInformationAsJSON(self, storage):
    """Writes a summary of sessions as machine-readable JSON.

    Args:
      storage (BaseStore): storage.
    """
    serializer = json_serializer.JSONAttributeContainerSerializer
    self._output_writer.Write('{')
    for index, session in enumerate(storage.GetSessions()):
      json_string = serializer.WriteSerialized(session)
      if index != 0:
        self._output_writer.Write(',\n')
      self._output_writer.Write('"session_{0:s}": {1:s} '.format(
          session.identifier, json_string))
    self._output_writer.Write('}')

  def _PrintTasksInformation(self, storage):
    """Prints information about the tasks.

    Args:
      storage (BaseStore): storage.
    """
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Tasks')

    for task_start, _ in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          task_start.timestamp)
      task_identifier = uuid.UUID(hex=task_start.identifier)
      table_view.AddRow([str(task_identifier), start_time])

    table_view.Write(self._output_writer)

  def CompareStores(self):
    """Compares the contents of two stores.

    Returns:
      bool: True if the content of the stores is identical.
    """
    storage_file = storage_factory.StorageFactory.CreateStorageFileForFile(
        self._storage_file_path)
    if not storage_file:
      logger.error(
          'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))
      return False

    try:
      storage_file.Open(path=self._storage_file_path, read_only=True)
    except IOError as exception:
      logger.error(
          'Unable to open storage file: {0:s} with error: {1!s}'.format(
              self._storage_file_path, exception))
      return False

    compare_storage_file = (
        storage_factory.StorageFactory.CreateStorageFileForFile(
            self._compare_storage_file_path))
    if not compare_storage_file:
      logger.error(
          'Format of storage file: {0:s} not supported'.format(
              self._compare_storage_file_path))
      return False

    try:
      compare_storage_file.Open(
          path=self._compare_storage_file_path, read_only=True)
    except IOError as exception:
      logger.error(
          'Unable to open storage file: {0:s} with error: {1!s}'.format(
              self._compare_storage_file_path, exception))
      storage_file.Close()
      return False

    try:
      result = self._CompareStores(storage_file, compare_storage_file)

    finally:
      compare_storage_file.Close()
      storage_file.Close()

    if result:
      self._output_writer.Write('Storage files are identical.\n')
    else:
      self._output_writer.Write('Storage files are different.\n')

    return result

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    loggers.ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    argument_helper_names = ['storage_file']
    if self._CanEnforceProcessMemoryLimit():
      argument_helper_names.append('process_resources')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=argument_helper_names)

    argument_parser.add_argument(
        '--compare', dest='compare_storage_file', type=str,
        action='store', default='', metavar='STORAGE_FILE', help=(
            'The path of the storage file to compare against.'))

    argument_parser.add_argument(
        '--output_format', '--output-format', dest='output_format', type=str,
        choices=['text', 'json'], action='store', default='text',
        metavar='FORMAT', help=(
            'Format of the output, the default is: text. Supported options: '
            'json, text.'))

    argument_parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true',
        default=False, help='Print verbose output.')

    argument_parser.add_argument(
        '-w', '--write', metavar='OUTPUTFILE', dest='write',
        help='Output filename.')

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    loggers.ConfigureLogging(
        debug_output=self._debug_mode, filename=self._log_file,
        quiet_mode=self._quiet_mode)

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._ParseInformationalOptions(options)

    self._verbose = getattr(options, 'verbose', False)

    self._output_filename = getattr(options, 'write', None)

    argument_helper_names = ['process_resources', 'storage_file']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    # TODO: move check into _CheckStorageFile.
    if not self._storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          'No such storage file: {0:s}.'.format(self._storage_file_path))

    compare_storage_file_path = self.ParseStringOption(
        options, 'compare_storage_file')
    if compare_storage_file_path:
      if not os.path.isfile(compare_storage_file_path):
        raise errors.BadConfigOption(
            'No such storage file: {0:s}.'.format(compare_storage_file_path))

      self._compare_storage_file_path = compare_storage_file_path
      self.compare_storage_information = True

    self._output_format = self.ParseStringOption(options, 'output_format')

    if self._output_filename:
      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            'Output file already exists: {0:s}.'.format(self._output_filename))
      output_file_object = open(self._output_filename, 'wb')
      self._output_writer = tools.FileObjectOutputWriter(output_file_object)

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

  def PrintStorageInformation(self):
    """Prints the storage information."""
    storage_file = storage_factory.StorageFactory.CreateStorageFileForFile(
        self._storage_file_path)
    if not storage_file:
      logger.error(
          'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))
      return

    try:
      storage_file.Open(path=self._storage_file_path, read_only=True)
    except IOError as exception:
      logger.error(
          'Unable to open storage file: {0:s} with error: {1!s}'.format(
              self._storage_file_path, exception))
      return

    try:
      if self._output_format == 'json':
        self._PrintStorageInformationAsJSON(storage_file)
      elif self._output_format == 'text':
        self._PrintStorageInformationAsText(storage_file)
    finally:
      storage_file.Close()
