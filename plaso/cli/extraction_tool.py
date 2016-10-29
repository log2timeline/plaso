# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

import os

import yara

from plaso.cli import storage_media_tool
from plaso.engine import engine
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3


class ExtractionTool(storage_media_tool.StorageMediaTool):
  """Class that implements an extraction CLI tool.

  Attributes:
    list_hashers (bool): True if the hashers should be listed.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
  """

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

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
    self._buffer_size = 0
    self._enable_profiling = False
    self._filter_object = None
    self._force_preprocessing = False
    self._hasher_names_string = None
    self._mount_path = None
    self._operating_system = None
    self._output_module = None
    self._parser_filter_expression = None
    self._preferred_year = None
    self._process_archives = False
    self._process_compressed_streams = True
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_JSON
    self._temporary_directory = None
    self._text_prepend = None
    self._yara_rules_string = None

    self.list_hashers = False
    self.list_parsers_and_plugins = False

  def _ParseExtractionOptions(self, options):
    """Parses the extraction options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._hasher_names_string = getattr(
        options, u'hashers', self._DEFAULT_HASHER_STRING)
    if isinstance(self._hasher_names_string, py2to3.STRING_TYPES):
      if self._hasher_names_string.lower() == u'list':
        self.list_hashers = True

    yara_rules_path = getattr(options, u'yara_rules_path', None)
    if yara_rules_path:
      try:
        with open(yara_rules_path, 'rb') as rules_file:
          yara_rules_string = rules_file.read()
        # We try to parse the rules here, to check that the definitions are
        # valid. We then pass the string definitions along to the workers, so
        # that they don't need read access to the rules file.
        yara.compile(source=yara_rules_string)
        self._yara_rules_string = yara_rules_string
      except IOError as exception:
        raise errors.BadConfigObject(
            u'Unable to read Yara rules file: {0:s}, error was: {1!s}'.format(
                yara_rules_path, exception))
      except yara.Error as exception:
        raise errors.BadConfigObject(
            u'Unable to parse Yara rules in: {0:s}, error was: {1!s}'.format(
                yara_rules_path, exception))

    parser_filter_expression = self.ParseStringOption(
        options, u'parsers', default_value=u'')
    self._parser_filter_expression = parser_filter_expression.replace(
        u'\\', u'/')

    if (isinstance(self._parser_filter_expression, py2to3.STRING_TYPES) and
        self._parser_filter_expression.lower() == u'list'):
      self.list_parsers_and_plugins = True

    self._force_preprocessing = getattr(options, u'preprocess', False)

    self._preferred_year = getattr(options, u'preferred_year', None)
    if self._preferred_year:
      try:
        self._preferred_year = int(self._preferred_year, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid preferred year: {0:s}.'.format(self._preferred_year))

    self._process_archives = getattr(options, u'process_archives', False)
    self._process_compressed_streams = getattr(
        options, u'process_compressed_streams', True)

    self._temporary_directory = getattr(options, u'temporary_directory', None)
    if (self._temporary_directory and
        not os.path.isdir(self._temporary_directory)):
      raise errors.BadConfigOption(
          u'No such temporary directory: {0:s}'.format(
              self._temporary_directory))

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

    queue_size = getattr(options, u'queue_size', None)
    if queue_size:
      try:
        self._queue_size = int(queue_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid queue size: {0:s}.'.format(queue_size))

  def _ParseProfilingOptions(self, options):
    """Parses the profiling options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._enable_profiling = getattr(options, u'enable_profiling', False)

    self._profiling_directory = getattr(options, u'profiling_directory', None)
    if (self._profiling_directory and
        not os.path.isdir(self._profiling_directory)):
      raise errors.BadConfigOption(
          u'No such profiling directory: {0:s}'.format(
              self._profiling_directory))

    profiling_sample_rate = getattr(options, u'profiling_sample_rate', None)
    if profiling_sample_rate:
      try:
        self._profiling_sample_rate = int(profiling_sample_rate, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid profile sample rate: {0:s}.'.format(
                profiling_sample_rate))

    self._profiling_type = getattr(options, u'profiling_type', u'all')

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

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--hashers', dest=u'hashers', type=str, action=u'store',
        default=self._DEFAULT_HASHER_STRING, metavar=u'HASHER_LIST', help=(
            u'Define a list of hashers to use by the tool. This is a comma '
            u'separated list where each entry is the name of a hasher, such as '
            u'"md5,sha256". "all" indicates that all hashers should be '
            u'enabled. "none" disables all hashers. Use "--hashers list" or '
            u'"--info" to list the available hashers.'))

    argument_group.add_argument(
        u'--yara_rules', u'--yara-rules', dest=u'yara_rules_path',
        type=str, metavar=u'PATH', action=u'store', help=(
            u'Path to a file containing Yara rules definitions.'))

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
        u'--temporary_directory', u'--temporary-directory',
        dest=u'temporary_directory', type=str, action=u'store',
        metavar=u'DIRECTORY', help=(
            u'Path to the directory that should be used to store temporary '
            u'files created during extraction.'))

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

  def AddProfilingOptions(self, argument_group):
    """Adds the profiling options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--profile', dest=u'enable_profiling', action=u'store_true',
        default=False, help=(
            u'Enable profiling. Intended usage is to troubleshoot memory '
            u'and performance issues.'))

    argument_group.add_argument(
        u'--profiling_directory', u'--profiling-directory',
        dest=u'profiling_directory', type=str, action=u'store',
        metavar=u'DIRECTORY', help=(
            u'Path to the directory that should be used to store the profiling '
            u'sample files. By default the sample files are stored in the '
            u'current working directory.'))

    argument_group.add_argument(
        u'--profiling_sample_rate', u'--profiling-sample-rate',
        dest=u'profiling_sample_rate', action=u'store', metavar=u'SAMPLE_RATE',
        default=0, help=(
            u'The profiling sample rate (defaults to a sample every {0:d} '
            u'files).').format(self._DEFAULT_PROFILING_SAMPLE_RATE))

    profiling_types = [u'all', u'parsers', u'processing', u'serializers']
    if engine.BaseEngine.SupportsMemoryProfiling():
      profiling_types.append(u'memory')

    argument_group.add_argument(
        u'--profiling_type', u'--profiling-type', dest=u'profiling_type',
        choices=sorted(profiling_types), action=u'store',
        metavar=u'TYPE', default=None, help=(
            u'The profiling type: "all", "memory", "parsers", "processing" '
            u'or "serializers".'))

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
    self._ParseProfilingOptions(options)
    self._ParseStorageOptions(options)
