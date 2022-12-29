# -*- coding: utf-8 -*-
"""The log2timeline CLI tool."""

import argparse
import sys
import textwrap

import plaso

# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import

from plaso.analyzers.hashers import manager as hashers_manager
from plaso.cli import extraction_tool
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.parsers import manager as parsers_manager


class Log2TimelineTool(extraction_tool.ExtractionTool):
  """Log2timeline CLI tool.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_archive_types (bool): True if the archive types should be listed.
    list_hashers (bool): True if the hashers should be listed.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
    list_profilers (bool): True if the profilers should be listed.
    show_info (bool): True if information about hashers, parsers, plugins,
        etc. should be shown.
  """

  NAME = 'log2timeline'
  DESCRIPTION = textwrap.dedent('\n'.join([
      '',
      ('log2timeline is a command line tool to extract events from '
       'individual '),
      'files, recursing a directory (e.g. mount point) or storage media ',
      'image or device.',
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
      '    log2timeline.py /cases/mycase/storage.plaso ímynd.dd',
      '',
      'Instead of answering questions, indicate some of the options on the',
      'command line (including data from particular VSS stores).',
      '    log2timeline.py --vss_stores 1,2 /cases/plaso_vss.plaso image.E01',
      '',
      'And that is how you build a timeline using log2timeline...',
      '']))

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes a log2timeline CLI tool.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(Log2TimelineTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_JSON

    self.dependencies_check = True
    self.list_archive_types = False
    self.list_hashers = False
    self.list_parsers_and_plugins = False
    self.list_profilers = False
    self.show_info = False

  def _GetPluginData(self):
    """Retrieves the version and various plugin information.

    Returns:
      dict[str, list[str]]: available parsers and plugins.
    """
    return_dict = {}

    return_dict['Versions'] = [
        ('plaso engine', plaso.__version__),
        ('python', sys.version)]

    hashers_information = hashers_manager.HashersManager.GetHashersInformation()
    parsers_information = parsers_manager.ParsersManager.GetParsersInformation()
    plugins_information = (
        parsers_manager.ParsersManager.GetParserPluginsInformation())
    presets_information = self._presets_manager.GetPresetsInformation()

    return_dict['Hashers'] = hashers_information
    return_dict['Parsers'] = parsers_information
    return_dict['Parser Plugins'] = plugins_information
    return_dict['Parser Presets'] = presets_information

    return return_dict

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

    argument_helper_names = [
        'archives', 'artifact_filters', 'extraction', 'filter_file', 'hashers',
        'parsers', 'yara_rules']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        extraction_group, names=argument_helper_names)

    self.AddStorageMediaImageOptions(extraction_group)
    self.AddExtractionOptions(extraction_group)
    self.AddVSSProcessingOptions(extraction_group)
    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group('informational arguments')

    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        '--info', dest='show_info', action='store_true', default=False,
        help='Print out information about supported plugins and parsers.')

    info_group.add_argument(
        '--use_markdown', '--use-markdown', dest='use_markdown',
        action='store_true', default=False, help=(
            'Output lists in Markdown format use in combination with '
            '"--hashers list", "--parsers list" or "--timezone list"'))

    info_group.add_argument(
        '--no_dependencies_check', '--no-dependencies-check',
        dest='dependencies_check', action='store_false', default=True,
        help='Disable the dependencies check.')

    self.AddLogFileOptions(info_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=['status_view'])

    processing_group = argument_parser.add_argument_group(
        'processing arguments')

    self.AddPerformanceOptions(processing_group)
    self.AddProcessingOptions(processing_group)

    processing_group.add_argument(
        '--sigsegv_handler', '--sigsegv-handler', dest='sigsegv_handler',
        action='store_true', default=False, help=(
            'Enables the SIGSEGV handler. WARNING this functionality is '
            'experimental and will a deadlock worker process if a real '
            'segfault is caught, but not signal SIGSEGV. This functionality '
            'is therefore primarily intended for debugging purposes'))

    profiling_group = argument_parser.add_argument_group('profiling arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        profiling_group, names=['profiling'])

    storage_group = argument_parser.add_argument_group('storage arguments')

    self.AddStorageOptions(storage_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        storage_group, names=['storage_format'])

    argument_parser.add_argument(
        self._SOURCE_OPTION, action='store', metavar='SOURCE', nargs='?',
        default=None, type=str, help=(
            'Path to a source device, file or directory. If the source is '
            'a supported storage media device or image file, archive file '
            'or a directory, the files within are processed recursively.'))

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

    self._command_line_arguments = self.GetCommandLineArguments()

    self._WaitUserWarning()

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
    # The extraction options are dependent on the data location.
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['data_location'])

    self._ReadParserPresetsFromFile()

    # Check the list options first otherwise required options will raise.
    argument_helper_names = ['archives', 'hashers', 'parsers', 'profiling']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseExtractionOptions(options)

    self.list_archive_types = self._archive_types_string == 'list'
    self.list_hashers = self._hasher_names_string == 'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == 'list'
    self.list_profilers = self._profilers == 'list'

    self.show_info = getattr(options, 'show_info', False)
    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    if getattr(options, 'use_markdown', False):
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_MARKDOWN

    self.dependencies_check = getattr(options, 'dependencies_check', True)

    if (self.list_archive_types or self.list_hashers or
        self.list_language_tags or self.list_parsers_and_plugins or
        self.list_profilers or self.list_time_zones or self.show_info or
        self.show_troubleshooting):
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = [
        'artifact_definitions', 'artifact_filters', 'extraction',
        'filter_file', 'status_view', 'storage_format', 'yara_rules']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    self._ParsePerformanceOptions(options)
    self._ParseProcessingOptions(options)

    self._storage_file_path = self.ParseStringOption(options, 'storage_file')
    if not self._storage_file_path:
      self._storage_file_path = self._GenerateStorageFileName()

    if not self._storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    serializer_format = getattr(
        options, 'serializer_format', definitions.SERIALIZER_FORMAT_JSON)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['status_view'])

    self._enable_sigsegv_handler = getattr(options, 'sigsegv_handler', False)

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

  def ShowInfo(self):
    """Shows information about available hashers, parsers, plugins, etc."""
    self._output_writer.Write(
        '{0:=^80s}\n'.format(' log2timeline/plaso information '))

    plugin_list = self._GetPluginData()
    for header, data in plugin_list.items():
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=['Name', 'Description'],
          title=header)
      for entry_header, entry_data in sorted(data):
        table_view.AddRow([entry_header, entry_data])
      table_view.Write(self._output_writer)
