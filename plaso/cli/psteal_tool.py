# -*- coding: utf-8 -*-
"""The psteal CLI tool."""

import argparse
import os
import textwrap

# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import

from plaso.cli import extraction_tool
from plaso.cli import tool_options
from plaso.cli.helpers import manager as helpers_manager
from plaso.containers import reports
from plaso.engine import configurations
from plaso.engine import engine
from plaso.lib import errors
from plaso.lib import loggers
from plaso.multi_process import output_engine as multi_output_engine
from plaso.parsers import manager as parsers_manager
from plaso.storage import factory as storage_factory


class PstealTool(
    extraction_tool.ExtractionTool,
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
    list_archive_types (bool): True if the archive types should be listed.
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
    self._number_of_analysis_reports = 0
    self._output_format = None
    self._parsers_manager = parsers_manager.ParsersManager
    self._preferred_year = None
    self._time_slice = None
    self._use_time_slicer = False

    self.dependencies_check = True
    self.list_archive_types = False
    self.list_hashers = False
    self.list_output_modules = False
    self.list_parsers_and_plugins = False

  def _CreateOutputAndFormattingProcessingConfiguration(self):
    """Creates an output and formatting processing configuration.

    Returns:
      ProcessingConfiguration: output and formatting processing configuration.
    """
    configuration = configurations.ProcessingConfiguration()
    configuration.custom_formatters_path = self._output_custom_formatters_path
    configuration.data_location = self._data_location
    configuration.debug_output = self._debug_mode
    configuration.dynamic_time = self._output_dynamic_time
    configuration.log_filename = self._log_file
    configuration.preferred_language = self._preferred_language
    configuration.preferred_time_zone = self._output_time_zone
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.profilers = self._profilers
    configuration.profiling.sample_rate = self._profiling_sample_rate

    return configuration

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

    argument_helper_names = ['archives', 'extraction', 'hashers', 'parsers']
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

    argument_helper_names = ['archives', 'hashers', 'parsers']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseExtractionOptions(options)

    self.list_archive_types = self._archive_types_string == 'list'
    self.list_hashers = self._hasher_names_string == 'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    self.dependencies_check = getattr(options, 'dependencies_check', True)

    # Check the list options first otherwise required options will raise.
    if (self.list_archive_types or self.list_hashers or
        self.list_language_tags or self.list_parsers_and_plugins or
        self.list_time_zones or self.show_troubleshooting):
      return

    # Check output modules after the other listable options, otherwise
    # it could raise with "requires an output file".
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['output_modules'])

    self.list_output_modules = self._output_format == 'list'
    if self.list_output_modules:
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = [
        'artifact_definitions', 'extraction', 'status_view']
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

  def ProcessStorage(self):
    """Processes a Plaso storage file.

    Raises:
      BadConfigOption: when a configuration parameter fails validation or the
          storage file cannot be opened with read access.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)
    session.preferred_language = self._preferred_language or 'en-US'

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

    configuration = self._CreateOutputAndFormattingProcessingConfiguration()

    if self._output_format != 'null':
      self._status_view.SetMode(self._status_view_mode)
      self._status_view.SetStatusFile(self._status_view_file)
      self._status_view.SetStorageFileInformation(self._storage_file_path)

      status_update_callback = (
          self._status_view.GetAnalysisStatusUpdateCallback())

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(
              self._storage_file_path))

      # TODO: add single process output and formatting engine support.
      output_engine = (
          multi_output_engine.OutputAndFormattingMultiProcessEngine())

      output_engine.ExportEvents(
          storage_reader, self._output_module, configuration,
          deduplicate_events=self._deduplicate_events,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      self._output_module.Close()
      self._output_module = None

    if self._quiet_mode:
      return

    self._output_writer.Write('Processing completed.\n')

    self._output_writer.Write('Storage file is {0:s}\n'.format(
        self._storage_file_path))
