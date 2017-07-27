# -*- coding: utf-8 -*-
"""The psteal CLI tool."""

import argparse
import collections
import datetime
import logging
import os
import sys
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context as dfvfs_context

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import

# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import

from plaso.cli import status_view
from plaso.cli import storage_media_tool
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.engine import single_process as single_process_engine
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.multi_processing import psort
from plaso.multi_processing import task_engine as multi_process_engine
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.parsers import manager as parsers_manager
from plaso.storage import zip_file as storage_zip_file


class PstealTool(
    storage_media_tool.StorageMediaTool,
    tool_options.AnalysisPluginOptions,
    tool_options.HashersOptions,
    tool_options.OutputModuleOptions,
    tool_options.ParsersOptions,
    tool_options.StorageFileOptions):
  """Psteal CLI tool.

  Psteal extract events from the provided source and stores them in an
  intermediate storage file. After extraction an output log file is created.
  This mimics the behaviour of the log2timeline.pl.
  The tool currently doesn't support any of the log2timeline or psort tools'
  flags.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
    list_hashers (bool): True if the hashers should be listed.
    list_language_identifiers (bool): True if information about the language
        identifiers should be shown.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
    list_output_modules (bool): True if information about the output modules
        should be shown.
  """

  NAME = u'psteal'

  # TODO: is textwrap.dedent or the join really needed here?
  DESCRIPTION = textwrap.dedent(u'\n'.join([
      u'',
      (u'psteal is a command line tool to extract events from individual '),
      u'files, recursing a directory (e.g. mount point) or storage media ',
      u'image or device. The output events will be stored in a storage file.',
      u'This tool will then read the output and process the events into a CSV ',
      u'file.',
      u'',
      u'More information can be gathered from here:',
      u'    https://github.com/log2timeline/plaso/wiki/Using-log2timeline',
      u'']))

  EPILOG = textwrap.dedent(u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Run the tool against a storage media image (full kitchen sink)',
      u'    psteal.py --source ímynd.dd -w imynd.timeline.txt',
      u'',
      u'And that is how you build a timeline using psteal...',
      u'']))

  # The window status-view mode has an annoying flicker on Windows,
  # hence we default to linear status-view mode instead.
  if sys.platform.startswith(u'win'):
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_LINEAR
  else:
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_WINDOW

  _SOURCE_TYPES_TO_PREPROCESS = frozenset([
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE])

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(PstealTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_plugins = None
    self._artifacts_registry = None
    self._command_line_arguments = None
    self._deduplicate_events = True
    self._enable_sigsegv_handler = False
    self._force_preprocessing = False
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._number_of_analysis_reports = 0
    self._number_of_extraction_workers = 0
    self._parser_filter_expression = None
    self._parsers_manager = parsers_manager.ParsersManager
    self._preferred_language = u'en-US'
    self._preferred_year = None
    self._resolver_context = dfvfs_context.Context()
    self._single_process_mode = False
    self._status_view_mode = self._DEFAULT_STATUS_VIEW_MODE
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._storage_file_path = None
    self._time_slice = None
    self._use_time_slicer = False
    self._use_zeromq = True
    self._yara_rules_string = None

    self.list_analysis_plugins = False
    self.list_hashers = False
    self.list_language_identifiers = False
    self.list_parsers_and_plugins = False
    self.list_output_modules = False

  def _CreateProcessingConfiguration(self):
    """Creates a processing configuration.

    Returns:
      ProcessingConfiguration: processing configuration.
    """
    # TODO: pass preferred_encoding.
    configuration = configurations.ProcessingConfiguration()
    configuration.credentials = self._credential_configurations
    configuration.debug_output = self._debug_mode
    configuration.extraction.hasher_names_string = self._hasher_names_string
    configuration.extraction.yara_rules_string = self._yara_rules_string
    configuration.filter_file = self._filter_file
    configuration.parser_filter_expression = self._parser_filter_expression
    configuration.preferred_year = self._preferred_year

    return configuration

  def _GenerateStorageFileName(self):
    """Generates a name for the storage file.

    The result use a timestamp and the basename of the source path.

    Raises:
      BadConfigOption: raised if the source path is not set.
    """
    if not self._source_path:
      raise errors.BadConfigOption(u'Please define a source (--source).')

    timestamp = datetime.datetime.now()
    datetime_string = timestamp.strftime(u'%Y%m%dT%H%M%S')

    source_path = os.path.abspath(self._source_path)
    source_name = os.path.basename(source_path)

    if source_path.endswith(os.path.sep):
      source_path = os.path.dirname(source_path)

    source_name = os.path.basename(source_path)

    if not source_name or source_name in (u'/', u'\\'):
      # The user passed the filesystem's root as source
      source_name = u'ROOT'

    return u'{0:s}-{1:s}.plaso'.format(datetime_string, source_name)

  def _PreprocessSources(self, extraction_engine):
    """Preprocesses the sources.

    Args:
      extraction_engine (BaseEngine): extraction engine to preprocess
          the sources.
    """
    logging.debug(u'Starting preprocessing.')

    try:
      extraction_engine.PreprocessSources(
          self._artifacts_registry, self._source_path_specs,
          resolver_context=self._resolver_context)

    except IOError as exception:
      logging.error(u'Unable to preprocess with error: {0:s}'.format(exception))

    logging.debug(u'Preprocessing done.')

  def _ParseOutputModuleOptions(self, options):
    """Parses the output module options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    preferred_time_zone = self._preferred_time_zone or u'UTC'

    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    output_mediator_object = output_mediator.OutputMediator(
        self._knowledge_base, formatter_mediator,
        preferred_encoding=self.preferred_encoding)
    output_mediator_object.SetTimezone(preferred_time_zone)

    try:
      self._output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, output_mediator_object)

    except IOError as exception:
      raise RuntimeError(
          u'Unable to create output module with error: {0:s}'.format(
              exception))

    if not self._output_module:
      raise RuntimeError(u'Missing output module.')

    if isinstance(self._output_module, output_interface.LinearOutputModule):
      if not self._output_filename:
        raise errors.BadConfigOption((
            u'Output format: {0:s} requires an output file').format(
                self._output_format))

      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            u'Output file already exists: {0:s}.'.format(self._output_filename))

      output_file_object = open(self._output_filename, u'wb')
      output_writer = tools.FileObjectOutputWriter(output_file_object)

      self._output_module.SetOutputWriter(output_writer)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self._output_module)

  def _PrintAnalysisReportsDetails(self, storage, number_of_analysis_reports):
    """Prints the details of the analysis reports.

    Args:
      storage (BaseStorage): storage writer.
      number_of_analysis_reports (int): number of analysis reports.
    """
    for index, analysis_report in enumerate(storage.GetAnalysisReports()):
      if index + 1 <= number_of_analysis_reports:
        continue

      title = u'Analysis report: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def AnalyzeEvents(self):
    """Analyzes events from a plaso storage file and generate a report.

    Raises:
      BadConfigOption: when a configuration parameter fails validation.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)

    storage_reader = storage_zip_file.ZIPStorageFileReader(
        self._storage_file_path)
    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    counter = collections.Counter()
    if self._output_format != u'null':
      self._status_view.SetMode(self._status_view_mode)
      self._status_view.SetStorageFileInformation(self._storage_file_path)

      status_update_callback = (
          self._status_view.GetAnalysisStatusUpdateCallback())

      storage_reader = storage_zip_file.ZIPStorageFileReader(
          self._storage_file_path)

      # TODO: add single processing support.
      analysis_engine = psort.PsortMultiProcessEngine(
          use_zeromq=self._use_zeromq)

      # TODO: pass configuration object.
      events_counter = analysis_engine.ExportEvents(
          self._knowledge_base, storage_reader, self._output_module,
          deduplicate_events=self._deduplicate_events,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      counter += events_counter

    for item, value in iter(session.analysis_reports_counter.items()):
      counter[item] = value

    if self._quiet_mode:
      return

    self._output_writer.Write(u'Processing completed.\n')

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Counter')
    for element, count in counter.most_common():
      if not element:
        element = u'N/A'
      table_view.AddRow([element, count])
    table_view.Write(self._output_writer)

    storage_reader = storage_zip_file.ZIPStorageFileReader(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(
        storage_reader, self._number_of_analysis_reports)

    self._output_writer.Write(u'Storage file is {0:s}\n'.format(
        self._storage_file_path))

  def ExtractEventsFromSources(self):
    """Processes the sources and extract events.

    This is a stripped down copy of tools/log2timeline.py that doesn't support
    the full set of flags. The defaults for these are hard coded in the
    constructor of this class.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self._CheckStorageFile(self._storage_file_path)

    scan_context = self.ScanSource()
    source_type = scan_context.source_type

    self._status_view.SetMode(self._status_view_mode)
    self._status_view.SetSourceInformation(
        self._source_path, source_type, filter_file=self._filter_file)

    status_update_callback = (
        self._status_view.GetExtractionStatusUpdateCallback())

    self._output_writer.Write(u'\n')
    self._status_view.PrintExtractionStatusHeader(None)
    self._output_writer.Write(u'Processing started.\n')

    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        filter_file=self._filter_file,
        preferred_encoding=self.preferred_encoding,
        preferred_time_zone=self._preferred_time_zone,
        preferred_year=self._preferred_year)

    storage_writer = storage_zip_file.ZIPStorageFileWriter(
        session, self._storage_file_path)

    configuration = self._CreateProcessingConfiguration()

    single_process_mode = self._single_process_mode
    if source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      # No need to multi process a single file source.
      single_process_mode = True

    if single_process_mode:
      extraction_engine = single_process_engine.SingleProcessEngine()
    else:
      extraction_engine = multi_process_engine.TaskMultiProcessEngine(
          use_zeromq=self._use_zeromq)

    # If the source is a directory or a storage media image
    # run pre-processing.
    if (self._force_preprocessing or
        source_type in self._SOURCE_TYPES_TO_PREPROCESS):
      self._PreprocessSources(extraction_engine)

    if not configuration.parser_filter_expression:
      operating_system = extraction_engine.knowledge_base.GetValue(
          u'operating_system')
      operating_system_product = extraction_engine.knowledge_base.GetValue(
          u'operating_system_product')
      operating_system_version = extraction_engine.knowledge_base.GetValue(
          u'operating_system_version')
      parser_filter_expression = (
          self._parsers_manager.GetPresetForOperatingSystem(
              operating_system, operating_system_product,
              operating_system_version))

      if parser_filter_expression:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

      configuration.parser_filter_expression = parser_filter_expression
      session.enabled_parser_names = list(
          self._parsers_manager.GetParserAndPluginNames(
              parser_filter_expression=configuration.parser_filter_expression))
      session.parser_filter_expression = configuration.parser_filter_expression

    if session.preferred_time_zone:
      try:
        extraction_engine.knowledge_base.SetTimeZone(
            session.preferred_time_zone)
      except ValueError:
        # pylint: disable=protected-access
        logging.warning(
            u'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                session.preferred_time_zone,
                extraction_engine.knowledge_base._time_zone.zone))

    filter_find_specs = None
    if configuration.filter_file:
      environment_variables = (
          extraction_engine.knowledge_base.GetEnvironmentVariables())
      filter_find_specs = frontend_utils.BuildFindSpecsFromFile(
          configuration.filter_file,
          environment_variables=environment_variables)

    processing_status = None
    if single_process_mode:
      logging.debug(u'Starting extraction in single process mode.')

      processing_status = extraction_engine.ProcessSources(
          self._source_path_specs, storage_writer, self._resolver_context,
          configuration, filter_find_specs=filter_find_specs,
          status_update_callback=status_update_callback)

    else:
      logging.debug(u'Starting extraction in multi process mode.')

      processing_status = extraction_engine.ProcessSources(
          session.identifier, self._source_path_specs, storage_writer,
          configuration,
          enable_sigsegv_handler=self._enable_sigsegv_handler,
          filter_find_specs=filter_find_specs,
          number_of_worker_processes=self._number_of_extraction_workers,
          status_update_callback=status_update_callback)

    self._status_view.PrintExtractionSummary(processing_status)

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=[u'storage_file'])

    extraction_group = argument_parser.add_argument_group(
        u'Extraction Arguments')

    argument_helper_names = [
        u'artifact_definitions', u'extraction', u'filter_file', u'hashers',
        u'parsers', u'yara_rules']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        extraction_group, names=argument_helper_names)

    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=[u'status_view'])

    input_group = argument_parser.add_argument_group(u'Input Arguments')
    input_group.add_argument(
        u'--source', dest=u'source', action=u'store',
        type=str, help=u'The source to process')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        input_group, names=[u'data_location'])

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_group, names=[u'language'])

    self.AddTimeZoneOption(output_group)

    output_format_group = argument_parser.add_argument_group(
        u'Output Format Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_format_group, names=[u'output_modules'])

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
      self._output_writer.Write(u'ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    return True

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # The extraction options are dependent on the data location.
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'data_location'])

    # Check the list options first otherwise required options will raise.

    # The output modules options are dependent on the preferred language
    # and preferred time zone options.
    self._ParseTimezoneOption(options)

    argument_helper_names = [
        u'analysis_plugins', u'hashers', u'language', u'output_modules',
        u'parsers']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self.list_hashers = self._hasher_names_string == u'list'
    self.list_language_identifiers = self._preferred_language == u'list'
    self.list_output_modules = self._output_format == u'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == u'list'

    if (self.list_analysis_plugins or self.list_hashers or
        self.list_language_identifiers or self.list_output_modules or
        self.list_parsers_and_plugins or self.list_timezones):
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = [
        u'artifact_definitions', u'extraction', u'status_view', u'storage_file',
        u'yara_rules']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    # These arguments are parsed from argparse.Namespace, so we can make
    # tests consistents with the log2timeline/psort ones.
    self._single_process_mode = getattr(options, u'single_process', False)

    if not self._storage_file_path:
      self._storage_file_path = self._GenerateStorageFileName()

    self._analysis_plugins = self._CreateAnalysisPlugins(options)
    self._output_module = self._CreateOutputModule(options)
