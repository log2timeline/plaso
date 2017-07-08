# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

import yara

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import

# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import

from plaso.analyzers.hashers import manager as hashers_manager
from plaso.cli import storage_media_tool
from plaso.cli import views
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.parsers import manager as parsers_manager
from plaso.parsers import presets as parsers_presets


class ExtractionTool(storage_media_tool.StorageMediaTool):
  """Class that implements an extraction CLI tool.

  Attributes:
    list_hashers (bool): True if the hashers should be listed.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
  """

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  # Enable the SHA256 hasher by default.
  _DEFAULT_HASHER_STRING = u'sha256'

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(ExtractionTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._artifacts_registry = None
    self._buffer_size = 0
    self._force_preprocessing = False
    self._hashers_manager = hashers_manager.HashersManager
    self._hasher_names_string = None
    self._mount_path = None
    self._operating_system = None
    self._output_module = None
    self._parser_filter_expression = None
    self._parsers_manager = parsers_manager.ParsersManager
    self._preferred_year = None
    self._process_archives = False
    self._process_compressed_streams = True
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_JSON
    self._text_prepend = None
    self._yara_rules_string = None

    self.list_hashers = False
    self.list_parsers_and_plugins = False

  def _GetParserPresetsInformation(self):
    """Retrieves the parser presets information.

    Returns:
      list[tuple]: contains:

        str: parser preset name
        str: parsers names corresponding to the preset
    """
    parser_presets_information = []
    for preset_name, parser_names in sorted(parsers_presets.CATEGORIES.items()):
      parser_presets_information.append((preset_name, u', '.join(parser_names)))

    return parser_presets_information

  def _ParseArtifactDefinitionsOption(self, options):
    """Parses the artifact definitions option.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    path = getattr(options, u'artifact_definitions_path', None)
    if not path:
      return

    self._artifacts_registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    try:
      self._artifacts_registry.ReadFromDirectory(reader, path)

    except (KeyError, artifacts_errors.FormatError) as exception:
      raise errors.BadConfigObject((
          u'Unable to read artifact definitions from: {0:s} with error: '
          u'{1!s}').format(path, exception))

  def _ParseExtractionOptions(self, options):
    """Parses the extraction options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._ParseArtifactDefinitionsOption(options)

    self._hasher_names_string = getattr(
        options, u'hashers', self._DEFAULT_HASHER_STRING)
    if isinstance(self._hasher_names_string, py2to3.STRING_TYPES):
      if self._hasher_names_string.lower() == u'list':
        self.list_hashers = True

    parser_filter_expression = self.ParseStringOption(
        options, u'parsers', default_value=u'')
    self._parser_filter_expression = parser_filter_expression.replace(
        u'\\', u'/')

    if (isinstance(self._parser_filter_expression, py2to3.STRING_TYPES) and
        self._parser_filter_expression.lower() == u'list'):
      self.list_parsers_and_plugins = True

    self._force_preprocessing = getattr(options, u'preprocess', False)

    self._preferred_year = self.ParseNumericOption(options, u'preferred_year')

    self._process_archives = getattr(options, u'process_archives', False)
    self._process_compressed_streams = getattr(
        options, u'process_compressed_streams', True)

    self._ParseYaraRulesOption(options)

  def _ParsePerformanceOptions(self, options):
    """Parses the performance options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._buffer_size = getattr(options, u'buffer_size', 0)
    if self._buffer_size:
      # TODO: turn this into a generic function that supports more size
      # suffixes both MB and MiB and also that does not allow m as a valid
      # indicator for MiB since m represents milli not Mega.
      try:
        if self._buffer_size[-1].lower() == u'm':
          self._buffer_size = int(self._buffer_size[:-1], 10)
          self._buffer_size *= self._BYTES_IN_A_MIB
        else:
          self._buffer_size = int(self._buffer_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid buffer size: {0:s}.'.format(self._buffer_size))

    self._queue_size = self.ParseNumericOption(options, u'queue_size')

  def _ParseStorageOptions(self, options):
    """Parses the storage options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    serializer_format = getattr(
        options, u'serializer_format', definitions.SERIALIZER_FORMAT_JSON)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          u'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

  def _ParseYaraRulesOption(self, options):
    """Parses the yara rules option.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    path = getattr(options, u'yara_rules_path', None)
    if not path:
      return

    try:
      with open(path, 'rb') as rules_file:
        self._yara_rules_string = rules_file.read()

    except IOError as exception:
      raise errors.BadConfigObject(
          u'Unable to read Yara rules file: {0:s} with error: {1!s}'.format(
              path, exception))

    try:
      # We try to parse the rules here, to check that the definitions are
      # valid. We then pass the string definitions along to the workers, so
      # that they don't need read access to the rules file.
      yara.compile(source=self._yara_rules_string)

    except yara.Error as exception:
      raise errors.BadConfigObject(
          u'Unable to parse Yara rules in: {0:s} with error: {1!s}'.format(
              path, exception))

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--artifact_definitions', u'--artifact-definitions',
        dest=u'artifact_definitions_path', type=str, metavar=u'PATH',
        action=u'store', help=(
            u'Path to a directory containing artifact definitions. Artifact '
            u'definitions can be used to describe and quickly collect data '
            u'data of interest, such as specific files or Windows Registry '
            u'keys.'))

    argument_group.add_argument(
        u'--hashers', dest=u'hashers', type=str, action=u'store',
        default=self._DEFAULT_HASHER_STRING, metavar=u'HASHER_LIST', help=(
            u'Define a list of hashers to use by the tool. This is a comma '
            u'separated list where each entry is the name of a hasher, such as '
            u'"md5,sha256". "all" indicates that all hashers should be '
            u'enabled. "none" disables all hashers. Use "--hashers list" or '
            u'"--info" to list the available hashers.'))

    # TODO: rename option name to parser_filter_expression.
    argument_group.add_argument(
        u'--parsers', dest=u'parsers', type=str, action=u'store',
        default=u'', metavar=u'PARSER_LIST', help=(
            u'Define a list of parsers to use by the tool. This is a comma '
            u'separated list where each entry can be either a name of a parser '
            u'or a parser list. Each entry can be prepended with an '
            u'exclamation mark to negate the selection (exclude it). The list '
            u'match is an exact match while an individual parser matching is '
            u'a case insensitive substring match, with support for glob '
            u'patterns. Examples would be: "reg" that matches the substring '
            u'"reg" in all parser names or the glob pattern "sky[pd]" that '
            u'would match all parsers that have the string "skyp" or "skyd" '
            u'in its name. All matching is case insensitive. Use "--parsers '
            u'list" or "--info" to list the available parsers.'))

    argument_group.add_argument(
        u'--preferred_year', u'--preferred-year', dest=u'preferred_year',
        action=u'store', default=None, metavar=u'YEAR', help=(
            u'When a format\'s timestamp does not include a year, e.g. '
            u'syslog, use this as the initial year instead of attempting '
            u'auto-detection.'))

    argument_group.add_argument(
        u'-p', u'--preprocess', dest=u'preprocess', action=u'store_true',
        default=False, help=(
            u'Turn on preprocessing. Preprocessing is turned on by default '
            u'when parsing image files, however if a mount point is being '
            u'parsed then this parameter needs to be set manually.'))

    argument_group.add_argument(
        u'--process_archives', u'--process-archives', dest=u'process_archives',
        action=u'store_true', default=False, help=(
            u'Process file entries embedded within archive files, such as '
            u'archive.tar and archive.zip. This can make processing '
            u'significantly slower.'))

    argument_group.add_argument(
        u'--skip_compressed_streams', u'--skip-compressed-streams',
        dest=u'process_compressed_streams', action=u'store_false', default=True,
        help=(
            u'Skip processing file content within compressed streams, such as '
            u'syslog.gz and syslog.bz2.'))

    argument_group.add_argument(
        u'--yara_rules', u'--yara-rules', dest=u'yara_rules_path',
        type=str, metavar=u'PATH', action=u'store', help=(
            u'Path to a file containing Yara rules definitions.'))

  def AddPerformanceOptions(self, argument_group):
    """Adds the performance options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--buffer_size', u'--buffer-size', u'--bs', dest=u'buffer_size',
        action=u'store', default=0, help=(
            u'The buffer size for the output (defaults to 196MiB).'))

    argument_group.add_argument(
        u'--queue_size', u'--queue-size', dest=u'queue_size', action=u'store',
        default=0, help=(
            u'The maximum number of queued items per worker '
            u'(defaults to {0:d})').format(self._DEFAULT_QUEUE_SIZE))

  def ListHashers(self):
    """Lists information about the available hashers."""
    hashers_information = self._hashers_manager.GetHashersInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Hashers')

    for name, description in sorted(hashers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ListParsersAndPlugins(self):
    """Lists information about the available parsers and plugins."""
    parsers_information = self._parsers_manager.GetParsersInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Parsers')

    for name, description in sorted(parsers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

    parser_names = self._parsers_manager.GetNamesOfParsersWithPlugins()
    for parser_name in parser_names:
      plugins_information = self._parsers_manager.GetParserPluginsInformation(
          parser_filter_expression=parser_name)

      table_title = u'Parser plugins: {0:s}'.format(parser_name)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=[u'Name', u'Description'],
          title=table_title)
      for name, description in sorted(plugins_information):
        table_view.AddRow([name, description])
      table_view.Write(self._output_writer)

    presets_information = self._GetParserPresetsInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Parsers and plugins'],
        title=u'Parser presets')
    for name, description in sorted(presets_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ExtractionTool, self).ParseOptions(options)
    self._ParseDataLocationOption(options)
    self._ParseFilterOptions(options)
    self._ParsePerformanceOptions(options)
    self._ParseStorageOptions(options)
