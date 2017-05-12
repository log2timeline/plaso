#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The log2timeline command line tool."""

import argparse
import logging
import multiprocessing
import os
import sys
import time
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions

from plaso import dependencies
from plaso.cli import extraction_tool
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.frontend import log2timeline
from plaso.engine import configurations
from plaso.lib import errors
from plaso.lib import pfilter


class Log2TimelineTool(extraction_tool.ExtractionTool):
  """Class that implements the log2timeline CLI tool.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_output_modules (bool): True if information about the output modules
        should be shown.
    show_info (bool): True if information about hashers, parsers, plugins,
        etc. should be shown.
  """

  NAME = u'log2timeline'
  DESCRIPTION = textwrap.dedent(u'\n'.join([
      u'',
      (u'log2timeline is a command line tool to extract events from '
       u'individual '),
      u'files, recursing a directory (e.g. mount point) or storage media ',
      u'image or device.',
      u'',
      u'More information can be gathered from here:',
      u'    https://github.com/log2timeline/plaso/wiki/Using-log2timeline',
      u'']))

  EPILOG = textwrap.dedent(u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Run the tool against a storage media image (full kitchen sink)',
      u'    log2timeline.py /cases/mycase/storage.plaso ímynd.dd',
      u'',
      u'Instead of answering questions, indicate some of the options on the',
      u'command line (including data from particular VSS stores).',
      (u'    log2timeline.py -o 63 --vss_stores 1,2 /cases/plaso_vss.plaso '
       u'image.E01'),
      u'',
      u'And that is how you build a timeline using log2timeline...',
      u'']))

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(Log2TimelineTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._command_line_arguments = None
    self._enable_sigsegv_handler = False
    self._filter_expression = None
    self._front_end = log2timeline.Log2TimelineFrontend()
    self._number_of_extraction_workers = 0
    self._output = None
    self._source_type = None
    self._source_type_string = u'UNKNOWN'
    self._status_view_mode = u'linear'
    self._stdout_output_writer = isinstance(
        self._output_writer, cli_tools.StdoutOutputWriter)
    self._temporary_directory = None
    self._text_prepend = None
    self._worker_memory_limit = None

    self.dependencies_check = True
    self.list_output_modules = False
    self.show_info = False

  def _DetermineSourceType(self):
    """Determines the source type."""
    scan_context = self.ScanSource()
    self._source_type = scan_context.source_type

    if self._source_type == dfvfs_definitions.SOURCE_TYPE_DIRECTORY:
      self._source_type_string = u'directory'

    elif self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      self._source_type_string = u'single file'

    elif self._source_type == (
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE):
      self._source_type_string = u'storage media device'

    elif self._source_type == (
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE):
      self._source_type_string = u'storage media image'

    else:
      self._source_type_string = u'UNKNOWN'

  def _GetMatcher(self, filter_expression):
    """Retrieves a filter object for a specific filter expression.

    Args:
      filter_expression (str): filter expression.

    Returns:
      A filter object (instance of objectfilter.TODO) or None.
    """
    try:
      parser = pfilter.BaseParser(filter_expression).Parse()
      return parser.Compile(pfilter.PlasoAttributeFilterImplementation)

    except errors.ParseError as exception:
      logging.error(
          u'Unable to create filter: {0:s} with error: {1:s}'.format(
              filter_expression, exception))

  def _GetStatusUpdateCallback(self):
    """Retrieves the status update callback function.

    Returns:
      function: status update callback function or None.
    """
    if self._status_view_mode == u'linear':
      return self._PrintStatusUpdateStream
    elif self._status_view_mode == u'window':
      return self._PrintStatusUpdate

  def _ParseOutputOptions(self, options):
    """Parses the output options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._output_module = self.ParseStringOption(options, u'output_module')
    if self._output_module == u'list':
      self.list_output_modules = True

    self._text_prepend = self.ParseStringOption(options, u'text_prepend')

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    use_zeromq = getattr(options, u'use_zeromq', True)
    self._front_end.SetUseZeroMQ(use_zeromq)

    self._single_process_mode = getattr(options, u'single_process', False)

    self._temporary_directory = getattr(options, u'temporary_directory', None)
    if (self._temporary_directory and
        not os.path.isdir(self._temporary_directory)):
      raise errors.BadConfigOption(
          u'No such temporary directory: {0:s}'.format(
              self._temporary_directory))

    self._worker_memory_limit = getattr(options, u'worker_memory_limit', None)
    self._number_of_extraction_workers = getattr(options, u'workers', 0)

    # TODO: add code to parse the worker options.

  def AddOutputOptions(self, argument_group):
    """Adds the output options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--output', dest=u'output_module', action=u'store', type=str,
        default=u'', help=(
            u'Bypass the storage module directly storing events according to '
            u'the output module. This means that the output will not be in the '
            u'pstorage format but in the format chosen by the output module. '
            u'Use "--output list" or "--info" to list the available output '
            u'modules. Note this feature is EXPERIMENTAL at this time '
            u'e.g. sqlite output does not yet work.'))

    argument_group.add_argument(
        u'-t', u'--text', dest=u'text_prepend', action=u'store', type=str,
        default=u'', metavar=u'TEXT', help=(
            u'Define a free form text string that is prepended to each path '
            u'to make it easier to distinguish one record from another in a '
            u'timeline (like c:\\, or host_w_c:\\)'))

  def AddProcessingOptions(self, argument_group):
    """Adds the processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--disable_zeromq', u'--disable-zeromq', action=u'store_false',
        dest=u'use_zeromq', default=True, help=(
            u'Disable queueing using ZeroMQ. A Multiprocessing queue will be '
            u'used instead.'))

    argument_group.add_argument(
        u'--single_process', u'--single-process', dest=u'single_process',
        action=u'store_true', default=False, help=(
            u'Indicate that the tool should run in a single process.'))

    argument_group.add_argument(
        u'--temporary_directory', u'--temporary-directory',
        dest=u'temporary_directory', type=str, action=u'store',
        metavar=u'DIRECTORY', help=(
            u'Path to the directory that should be used to store temporary '
            u'files created during extraction.'))

    argument_group.add_argument(
        u'--worker-memory-limit', u'--worker_memory_limit',
        dest=u'worker_memory_limit', action=u'store', type=int,
        metavar=u'SIZE', help=(
            u'Maximum amount of memory a worker process is allowed to consume. '
            u'[defaults to 2 GiB]'))

    argument_group.add_argument(
        u'--workers', dest=u'workers', action=u'store', type=int, default=0,
        help=(u'The number of worker processes [defaults to available system '
              u'CPUs minus one].'))

  def ListHashers(self):
    """Lists information about the available hashers."""
    hashers_information = self._front_end.GetHashersInformation()

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Hashers')

    for name, description in sorted(hashers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ListOutputModules(self):
    """Lists the output modules."""
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Output Modules')
    for name, output_class in self._front_end.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(self._front_end.GetDisabledOutputClasses())
    if not disabled_classes:
      return

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Disabled Output Modules')
    for name, output_class in disabled_classes:
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

  def ListParsersAndPlugins(self):
    """Lists information about the available parsers and plugins."""
    parsers_information = self._front_end.GetParsersInformation()

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Parsers')

    for name, description in sorted(parsers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

    for parser_name in self._front_end.GetNamesOfParsersWithPlugins():
      plugins_information = self._front_end.GetParserPluginsInformation(
          parser_filter_expression=parser_name)

      table_title = u'Parser plugins: {0:s}'.format(parser_name)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=[u'Name', u'Description'],
          title=table_title)
      for name, description in sorted(plugins_information):
        table_view.AddRow([name, description])
      table_view.Write(self._output_writer)

    presets_information = self._front_end.GetParserPresetsInformation()

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Parsers and plugins'],
        title=u'Parser presets')
    for name, description in sorted(presets_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    extraction_group = argument_parser.add_argument_group(
        u'Extraction Arguments')

    self.AddExtractionOptions(extraction_group)
    self.AddFilterOptions(extraction_group)
    self.AddStorageMediaImageOptions(extraction_group)
    self.AddTimeZoneOption(extraction_group)
    self.AddVSSProcessingOptions(extraction_group)
    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        u'--info', dest=u'show_info', action=u'store_true', default=False,
        help=u'Print out information about supported plugins and parsers.')

    info_group.add_argument(
        u'--use_markdown', u'--use-markdown', dest=u'use_markdown',
        action=u'store_true', default=False, help=(
            u'Output lists in Markdown format use in combination with '
            u'"--hashers list", "--parsers list" or "--timezone list"'))

    info_group.add_argument(
        u'--no_dependencies_check', u'--no-dependencies-check',
        dest=u'dependencies_check', action=u'store_false', default=True,
        help=u'Disable the dependencies check.')

    self.AddLogFileOptions(info_group)

    # The window status-view mode has an annoying flicker on Windows,
    # hence we default to linear status-view mode instead.
    if sys.platform.startswith(u'win'):
      default_status_view = u'linear'
    else:
      default_status_view = u'window'

    info_group.add_argument(
        u'--status_view', u'--status-view', dest=u'status_view_mode',
        choices=[u'linear', u'none', u'window'], action=u'store',
        metavar=u'TYPE', default=default_status_view, help=(
            u'The processing status view mode: "linear", "none" or "window".'))

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    self.AddOutputOptions(output_group)

    processing_group = argument_parser.add_argument_group(
        u'Processing Arguments')

    self.AddDataLocationOption(processing_group)
    self.AddPerformanceOptions(processing_group)
    self.AddProfilingOptions(processing_group)
    self.AddProcessingOptions(processing_group)

    processing_group.add_argument(
        u'--sigsegv_handler', u'--sigsegv-handler', dest=u'sigsegv_handler',
        action=u'store_true', default=False, help=(
            u'Enables the SIGSEGV handler. WARNING this functionality is '
            u'experimental and will a deadlock worker process if a real '
            u'segfault is caught, but not signal SIGSEGV. This functionality '
            u'is therefore primarily intended for debugging purposes'))

    argument_parser.add_argument(
        u'output', action=u'store', metavar=u'STORAGE_FILE', nargs=u'?',
        type=str, help=(
            u'The path to the output file, if the file exists it will get '
            u'appended to.'))

    argument_parser.add_argument(
        self._SOURCE_OPTION, action=u'store', metavar=u'SOURCE', nargs=u'?',
        default=None, type=str, help=(
            u'The path to the source device, file or directory. If the source '
            u'is a supported storage media device or image file, archive file '
            u'or a directory, the files within are processed recursively.'))

    argument_parser.add_argument(
        u'filter', action=u'store', metavar=u'FILTER', nargs=u'?', default=None,
        type=str, help=(
            u'A filter that can be used to filter the dataset before it '
            u'is written into storage. More information about the filters '
            u'and its usage can be found here: http://plaso.kiddaland.'
            u'net/usage/filters'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == u'ascii':
      logging.warning(
          u'The preferred encoding of your system is ASCII, which is not '
          u'optimal for the typically non-ASCII characters that need to be '
          u'parsed and processed. The tool will most likely crash and die, '
          u'perhaps in a way that may not be recoverable. A five second delay '
          u'is introduced to give you time to cancel the runtime and '
          u'reconfigure your preferred encoding, otherwise continue at own '
          u'risk.')
      time.sleep(5)

    if self._process_archives:
      logging.warning(
          u'Scanning archive files currently can cause deadlock. Continue at '
          u'your own risk.')
      time.sleep(5)

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write(u'ERROR: {0:s}'.format(exception))
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    self._command_line_arguments = self.GetCommandLineArguments()

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # Check the list options first otherwise required options will raise.
    self._ParseExtractionOptions(options)
    self._ParseOutputOptions(options)
    self._ParseProfilingOptions(options)
    self._ParseTimezoneOption(options)

    self.show_info = getattr(options, u'show_info', False)

    if getattr(options, u'use_markdown', False):
      self._views_format_type = cli_views.ViewsFactory.FORMAT_TYPE_MARKDOWN

    self.dependencies_check = getattr(options, u'dependencies_check', True)

    if (self.list_hashers or self.list_output_modules or
        self.list_parsers_and_plugins or self.list_profilers or
        self.list_timezones or self.show_info):
      return

    super(Log2TimelineTool, self).ParseOptions(options)
    self._ParseOutputOptions(options)
    self._ParseProcessingOptions(options)

    format_string = (
        u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
        u'<%(module)s> %(message)s')

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self.ParseLogFileOptions(options)
    self._ConfigureLogging(
        filename=self._log_file, format_string=format_string,
        log_level=logging_level)

    if self._debug_mode:
      logging_filter = log2timeline.LoggingFilter()
      root_logger = logging.getLogger()
      root_logger.addFilter(logging_filter)

    self._output = self.ParseStringOption(options, u'output')
    if not self._output:
      raise errors.BadConfigOption(u'No output defined.')

    # TODO: where is this defined?
    self._operating_system = getattr(options, u'os', None)

    if self._operating_system:
      self._mount_path = getattr(options, u'filename', None)

    self._filter_expression = self.ParseStringOption(options, u'filter')
    if self._filter_expression:
      # TODO: refactor self._filter_object out the tool into the frontend.
      self._filter_object = self._GetMatcher(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    self._status_view_mode = getattr(options, u'status_view_mode', u'linear')
    self._enable_sigsegv_handler = getattr(options, u'sigsegv_handler', False)

  def ProcessSources(self):
    """Processes the sources.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self._DetermineSourceType()

    self._output_writer.Write(u'\n')
    self._PrintStatusHeader()

    self._output_writer.Write(u'Processing started.\n')

    status_update_callback = self._GetStatusUpdateCallback()

    session = self._front_end.CreateSession(
        command_line_arguments=self._command_line_arguments,
        filter_file=self._filter_file,
        preferred_encoding=self.preferred_encoding,
        preferred_time_zone=self._preferred_time_zone,
        preferred_year=self._preferred_year)

    storage_writer = self._front_end.CreateStorageWriter(session, self._output)
    # TODO: handle errors.BadConfigOption

    # TODO: pass preferred_encoding.
    configuration = configurations.ProcessingConfiguration()
    configuration.credentials = self._credential_configurations
    configuration.debug_output = self._debug_mode
    configuration.event_extraction.filter_object = self._filter_object
    configuration.event_extraction.text_prepend = self._text_prepend
    configuration.extraction.hasher_names_string = self._hasher_names_string
    configuration.extraction.process_archives = self._process_archives
    configuration.extraction.process_compressed_streams = (
        self._process_compressed_streams)
    configuration.extraction.yara_rules_string = self._yara_rules_string
    configuration.filter_file = self._filter_file
    configuration.filter_object = self._filter_object
    configuration.input_source.mount_path = self._mount_path
    configuration.parser_filter_expression = self._parser_filter_expression
    configuration.preferred_year = self._preferred_year
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers
    configuration.temporary_directory = self._temporary_directory

    processing_status = self._front_end.ProcessSources(
        session, storage_writer, self._source_path_specs, self._source_type,
        configuration, enable_sigsegv_handler=self._enable_sigsegv_handler,
        force_preprocessing=self._force_preprocessing,
        number_of_extraction_workers=self._number_of_extraction_workers,
        single_process_mode=self._single_process_mode,
        status_update_callback=status_update_callback,
        worker_memory_limit=self._worker_memory_limit)

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

  def ShowInfo(self):
    """Shows information about available hashers, parsers, plugins, etc."""
    self._output_writer.Write(
        u'{0:=^80s}\n'.format(u' log2timeline/plaso information '))

    plugin_list = self._front_end.GetPluginData()
    for header, data in plugin_list.items():
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=[u'Name', u'Description'],
          title=header)
      for entry_header, entry_data in sorted(data):
        table_view.AddRow([entry_header, entry_data])
      table_view.Write(self._output_writer)


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  tool = Log2TimelineTool()

  if not tool.ParseArguments():
    return False

  if tool.show_info:
    tool.ShowInfo()
    return True

  have_list_option = False
  if tool.list_hashers:
    tool.ListHashers()
    have_list_option = True

  if tool.list_parsers_and_plugins:
    tool.ListParsersAndPlugins()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_profilers:
    tool.ListProfilers()
    have_list_option = True

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if have_list_option:
    return True

  if tool.dependencies_check and not dependencies.CheckDependencies(
      verbose_output=False):
    return False

  try:
    tool.ProcessSources()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except (errors.BadConfigOption, errors.SourceScannerError) as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
