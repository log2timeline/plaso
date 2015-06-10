# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

import argparse

from plaso.cli import storage_media_tool
from plaso.engine import engine
from plaso.lib import definitions
from plaso.lib import errors


class ExtractionTool(storage_media_tool.StorageMediaTool):
  """Class that implements an extraction CLI tool."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(ExtractionTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._buffer_size = 0
    self._enable_profiling = False
    self._filter_object = None
    self._hasher_names_string = None
    self._mount_path = None
    self._old_preprocess = False
    self._operating_system = None
    self._output_module = None
    self._parser_filter_string = None
    self._process_archive_files = False
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_PROTOBUF
    self._text_prepend = None

  def _ParseExtractionOptions(self, options):
    """Parses the extraction options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._hasher_names_string = getattr(options, u'hashers', u'')
    self._parser_filter_string = getattr(options, u'parsers', u'')

    # TODO: preprocess.

    self._old_preprocess = getattr(options, u'old_preprocess', False)

    self._process_archive_files = getattr(options, u'scan_archives', False)

  def _ParsePerformanceOptions(self, options):
    """Parses the performance options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

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
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._enable_profiling = getattr(options, u'enable_profiling', False)

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
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    serializer_format = getattr(
        options, u'serializer_format', definitions.SERIALIZER_FORMAT_PROTOBUF)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          u'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--hashers', dest=u'hashers', type=str, action=u'store', default=u'',
        metavar=u'HASHER_LIST', help=(
            u'Define a list of hashers to use by the tool. This is a comma '
            u'separated list where each entry is the name of a hasher. eg. md5,'
            u'sha256.'))

    # TODO: rename option name to parser_filter_string.
    argument_group.add_argument(
        u'--parsers', dest=u'parsers', type=unicode, action=u'store',
        default=u'', metavar=u'PARSER_LIST', help=(
            u'Define a list of parsers to use by the tool. This is a comma '
            u'separated list where each entry can be either a name of a parser '
            u'or a parser list. Each entry can be prepended with a minus sign '
            u'to negate the selection (exclude it). The list match is an '
            u'exact match while an individual parser matching is a case '
            u'insensitive substring match, with support for glob patterns. '
            u'Examples would be: "reg" that matches the substring "reg" in '
            u'all parser names or the glob pattern "sky[pd]" that would match '
            u'all parsers that have the string "skyp" or "skyd" in its name. '
            u'All matching is case insensitive.'))

    argument_group.add_argument(
        u'-p', u'--preprocess', dest=u'preprocess', action=u'store_true',
        default=False, help=(
            u'Turn on preprocessing. Preprocessing is turned on by default '
            u'when parsing image files, however if a mount point is being '
            u'parsed then this parameter needs to be set manually.'))

    argument_group.add_argument(
        u'--scan_archives', dest=u'scan_archives', action=u'store_true',
        default=False, help=argparse.SUPPRESS)

    # This option is "hidden" for the time being, still left in there for
    # testing purposes, but hidden from the tool usage and help messages.
    #    help=(u'Indicate that the tool should try to open files to extract '
    #          u'embedded files within them, for instance to extract files '
    #          u'from compressed containers, etc. Be AWARE THAT THIS IS '
    #          u'EXTREMELY SLOW.'))

    argument_group.add_argument(
        '--use_old_preprocess', '--use-old-preprocess', dest='old_preprocess',
        action='store_true', default=False, help=(
            u'Only used in conjunction when appending to a previous storage '
            u'file. When this option is used then a new preprocessing object '
            u'is not calculated and instead the last one that got added to '
            u'the storage file is used. This can be handy when parsing an '
            u'image that contains more than a single partition.'))

  def AddPerformanceOptions(self, argument_group):
    """Adds the performance options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--buffer_size', u'--buffer-size', u'--bs', dest=u'buffer_size',
        action=u'store', default=0,
        help=u'The buffer size for the output (defaults to 196MiB).')

    argument_group.add_argument(
        u'--queue_size', u'--queue-size', dest=u'queue_size', action=u'store',
        default=0, help=(
            u'The maximum number of queued items per worker '
            u'(defaults to {0:d})').format(self._DEFAULT_QUEUE_SIZE))

  def AddProfilingOptions(self, argument_group):
    """Adds the profiling options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--profile', dest=u'enable_profiling', action=u'store_true',
        default=False, help=(
            u'Enable profiling. Intended usage is to troubleshoot memory '
            u'and performance issues.'))

    argument_group.add_argument(
        u'--profiling_sample_rate', u'--profiling-sample-rate',
        dest=u'profiling_sample_rate', action=u'store', metavar=u'SAMPLE_RATE',
        default=0, help=(
            u'The profiling sample rate (defaults to a sample every {0:d} '
            u'files).').format(self._DEFAULT_PROFILING_SAMPLE_RATE))

    profiling_types = [u'all', u'parsers', u'serializers']
    if engine.BaseEngine.SupportsMemoryProfiling():
      profiling_types.append(u'memory')

    argument_group.add_argument(
        u'--profiling_type', u'--profiling-type', dest=u'profiling_type',
        choices=sorted(profiling_types), action=u'store',
        metavar=u'TYPE', default=None, help=(
            u'The profiling type: "all", "memory", "parsers" or '
            u'"serializers".'))

  def AddStorageOptions(self, argument_group):
    """Adds the storage options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--serializer-format', u'--serializer_format', action=u'store',
        dest=u'serializer_format', default=u'json', metavar=u'FORMAT', help=(
            u'By default the storage uses JSON for serializing event '
            u'objects. This parameter can be used to change that behavior. '
            u'The choices are "proto" and "json".'))

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ExtractionTool, self).ParseOptions(options)
    self._ParseExtractionOptions(options)
    self._ParseDataLocationOption(options)
    self._ParseFilterOptions(options)
    self._ParsePerformanceOptions(options)
    self._ParseProfilingOptions(options)
    self._ParseStorageOptions(options)
