# -*- coding: utf-8 -*-
"""The psteal CLI tool."""

import argparse
import collections
import os
import textwrap

from dfdatetime import posix_time as dfdatetime_posix_time

# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import

from plaso.cli import extraction_tool
from plaso.cli import logger
from plaso.cli import tool_options
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.containers import reports
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.lib import errors
from plaso.lib import loggers
from plaso.multi_process import output_engine as multi_output_engine
from plaso.parsers import manager as parsers_manager
from plaso.storage import factory as storage_factory


class PstealTool(
    extraction_tool.ExtractionTool,
    tool_options.HashersOptions,
    tool_options.OutputModuleOptions,
    tool_options.StorageFileOptions):
  """Psteal CLI tool.

  Psteal extract events from the provided source and stores them in an
  intermediate storage file. After extraction an output log file is created.
  This mimics the behavior of the log2timeline.pl.

  The tool currently doesn't support any of the log2timeline or psort tools'
  flags.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_hashers (bool): True if the hashers should be listed.
    list_output_modules (bool): True if information about the output modules
        should be shown.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
  """

  NAME = 'psteal'

  # TODO: is textwrap.dedent or the join really needed here?
  DESCRIPTION = textwrap.dedent('\n'.join([
      '',
      'psteal is a command line tool to extract events from individual ',
      'files, recursing a directory (e.g. mount point) or storage media ',
      'image or device. The output events will be stored in a storage file.',
      'This tool will then read the output and process the events into a CSV ',
      'file.',
      '',
      'More information can be gathered from here:',
      '    https://plaso.readthedocs.io/en/latest/sources/user/'
      'Using-log2timeline.html',
      '']))

  EPILOG = textwrap.dedent('\n'.join([
      '',
      'Example usage:',
      '',
      'Run the tool against a storage media image (full kitchen sink)',
      '    psteal.py --source ímynd.dd -w imynd.timeline.txt',
      '',
      'And that is how you build a timeline using psteal...',
      '']))

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE

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
    self._artifacts_registry = None
    self._deduplicate_events = True
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._number_of_analysis_reports = 0
    self._output_format = None
    self._parsers_manager = parsers_manager.ParsersManager
    self._preferred_year = None
    self._time_slice = None
    self._use_time_slicer = False

    self.dependencies_check = True
    self.list_hashers = False
    self.list_output_modules = False
    self.list_parsers_and_plugins = False

  def _PrintAnalysisReportsDetails(
      self, storage_reader, number_of_analysis_reports):
    """Prints the details of the analysis reports.

    Args:
      storage_reader (StorageReader): storage reader.
      number_of_analysis_reports (int): number of analysis reports.
    """
    generator = storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

    for index, analysis_report in enumerate(generator):
      if index + 1 <= number_of_analysis_reports:
        continue

      date_time_string = None
      if analysis_report.time_compiled is not None:
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=analysis_report.time_compiled)
        date_time_string = date_time.CopyToDateTimeStringISO8601()

      title = 'Analysis report: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Name plugin', analysis_report.plugin_name or 'N/A'])
      table_view.AddRow(['Date and time', date_time_string or 'N/A'])
      table_view.AddRow(['Event filter', analysis_report.event_filter or 'N/A'])

      if not analysis_report.analysis_counter:
        table_view.AddRow(['Text', analysis_report.text or ''])
      else:
        table_view.AddRow(['Results', ''])
        for key, value in sorted(analysis_report.analysis_counter.items()):
          table_view.AddRow([key, value])

      table_view.Write(self._output_writer)

  def AddStorageOptions(self, argument_group):  # pylint: disable=arguments-renamed
    """Adds the storage options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--storage_file', '--storage-file', dest='storage_file', metavar='PATH',
        type=str, default=None, help=(
            'The path of the storage file. If not specified, one will be made '
            'in the form <timestamp>-<source>.plaso'))

  def AnalyzeEvents(self):
    """Analyzes events from a plaso storage file and generate a report.

    Raises:
      BadConfigOption: when a configuration parameter fails validation or the
          storage file cannot be opened with read access.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    if not storage_reader:
      raise errors.BadConfigOption(
          'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))

    try:
      self._number_of_analysis_reports = (
          storage_reader.GetNumberOfAttributeContainers(
              self._CONTAINER_TYPE_ANALYSIS_REPORT))

    finally:
      storage_reader.Close()

    configuration = self._CreateProcessingConfiguration(
        self._knowledge_base)

    counter = collections.Counter()
    if self._output_format != 'null':
      self._status_view.SetMode(self._status_view_mode)
      self._status_view.SetStorageFileInformation(self._storage_file_path)

      status_update_callback = (
          self._status_view.GetAnalysisStatusUpdateCallback())

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(
              self._storage_file_path))

      preferred_language = self._knowledge_base.language
      if self._preferred_language:
        preferred_language = self._preferred_language

      if preferred_language:
        try:
          self._output_mediator.SetPreferredLanguageIdentifier(
              preferred_language)
        except (KeyError, TypeError):
          logger.warning('Unable to to set preferred language: {0!s}.'.format(
              preferred_language))

      self._output_module.SetStorageReader(storage_reader)

      # TODO: add single process output and formatting engine support.
      output_engine = (
          multi_output_engine.OutputAndFormattingMultiProcessEngine())

      output_engine.ExportEvents(
          self._knowledge_base, storage_reader, self._output_module,
          configuration, deduplicate_events=self._deduplicate_events,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      self._output_module.Close()
      self._output_module = None

    for item, value in session.analysis_reports_counter.items():
      counter[item] = value

    if self._quiet_mode:
      return

    self._output_writer.Write('Processing completed.\n')

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Counter')
    for element, count in counter.most_common():
      if not element:
        element = 'N/A'
      table_view.AddRow([element, count])
    table_view.Write(self._output_writer)

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(
        storage_reader, self._number_of_analysis_reports)

    self._output_writer.Write('Storage file is {0:s}\n'.format(
        self._storage_file_path))

  def ParseArguments(self, arguments):
    """Parses the command line arguments.

    Args:
      arguments (list[str]): command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    loggers.ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    data_location_group = argument_parser.add_argument_group(
        'data location arguments')

    argument_helper_names = ['artifact_definitions', 'data_location']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        data_location_group, names=argument_helper_names)

    extraction_group = argument_parser.add_argument_group(
        'extraction arguments')

    argument_helper_names = ['extraction', 'hashers', 'parsers']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        extraction_group, names=argument_helper_names)

    self.AddStorageOptions(extraction_group)
    self.AddStorageMediaImageOptions(extraction_group)
    self.AddExtractionOptions(extraction_group)
    self.AddVSSProcessingOptions(extraction_group)
    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group('informational arguments')

    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        '--no_dependencies_check', '--no-dependencies-check',
        dest='dependencies_check', action='store_false', default=True,
        help='Disable the dependencies check.')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=['status_view'])

    input_group = argument_parser.add_argument_group('input arguments')
    input_group.add_argument(
        '--source', dest='source', action='store',
        type=str, help='The source to process')

    output_group = argument_parser.add_argument_group('output arguments')

    self.AddOutputOptions(output_group)

    output_format_group = argument_parser.add_argument_group(
        'output format arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_format_group, names=['output_modules'])

    processing_group = argument_parser.add_argument_group(
        'processing arguments')

    self.AddPerformanceOptions(processing_group)
    self.AddProcessingOptions(processing_group)

    try:
      options = argument_parser.parse_args(arguments)
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == 'ascii':
      self._PrintUserWarning((
          'the preferred encoding of your system is ASCII, which is not '
          'optimal for the typically non-ASCII characters that need to be '
          'parsed and processed. This will most likely result in an error.'))

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    self._WaitUserWarning()

    loggers.ConfigureLogging(
        debug_output=self._debug_mode, filename=self._log_file,
        quiet_mode=self._quiet_mode)

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
        options, self, names=['data_location'])

    self._ReadParserPresetsFromFile()

    # The output modules options are dependent on the preferred_language
    # and output_time_zone options.
    self._ParseOutputOptions(options)

    argument_helper_names = ['artifact_definitions', 'hashers', 'parsers']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseExtractionOptions(options)

    self.list_hashers = self._hasher_names_string == 'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    self.dependencies_check = getattr(options, 'dependencies_check', True)

    # Check the list options first otherwise required options will raise.
    if (self.list_hashers or self.list_language_identifiers or
        self.list_parsers_and_plugins or self.list_time_zones or
        self.show_troubleshooting):
      return

    # Check output modules after the other listable options, otherwise
    # it could raise with "requires an output file".
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['output_modules'])

    self.list_output_modules = self._output_format == 'list'
    if self.list_output_modules:
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = ['extraction', 'status_view']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    self._ParsePerformanceOptions(options)
    self._ParseProcessingOptions(options)

    self._storage_file_path = self.ParseStringOption(options, 'storage_file')
    if not self._storage_file_path:
      self._storage_file_path = self._GenerateStorageFileName()

    self._output_filename = getattr(options, 'write', None)

    if not self._output_filename:
      raise errors.BadConfigOption((
          'Output format: {0:s} requires an output file '
          '(-w OUTPUT_FILE)').format(self._output_format))

    if os.path.exists(self._output_filename):
      raise errors.BadConfigOption(
          'Output file already exists: {0:s}.'.format(self._output_filename))

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

    self._output_module = self._CreateOutputModule(options)
