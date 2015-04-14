# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

import os

from plaso.cli import storage_media_tool
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import pfilter

import pytz


class ExtractionTool(storage_media_tool.StorageMediaTool):
  """Class that implements an extraction CLI tool."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

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
    self._debug_mode = False
    self._enable_profiling = False
    self._filter_expression = None
    self._filter_file = None
    self._filter_object = None
    self._mount_path = None
    self._old_preprocess = False
    self._operating_system = None
    self._output_module = None
    self._process_archive_files = False
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_PROTOBUF
    self._text_prepend = None
    self._timezone = pytz.utc

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--use_old_preprocess', '--use-old-preprocess', dest='old_preprocess',
        action='store_true', default=False, help=(
            u'Only used in conjunction when appending to a previous storage '
            u'file. When this option is used then a new preprocessing object '
            u'is not calculated and instead the last one that got added to '
            u'the storage file is used. This can be handy when parsing an '
            u'image that contains more than a single partition.'))

  def AddInformationalOptions(self, argument_group):
    """Adds the informational options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '-d', '--debug', dest='debug', action='store_true', default=False,
        help=(
            u'Enable debug mode. Intended for troubleshooting parsing '
            u'issues.'))

  def AddPerformanceOptions(self, argument_group):
    """Adds the performance options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--buffer_size', '--buffer-size', '--bs', dest='buffer_size',
        action='store', default=0,
        help=u'The buffer size for the output (defaults to 196MiB).')

    argument_group.add_argument(
        '--queue_size', '--queue-size', dest='queue_size', action='store',
        default=0, help=(
            u'The maximum number of queued items per worker '
            u'(defaults to {0:d})').format(self._DEFAULT_QUEUE_SIZE))

    # TODO: move SupportsProfiling to engine.
    if worker.BaseEventExtractionWorker.SupportsProfiling():
      argument_group.add_argument(
          '--profile', dest='enable_profiling', action='store_true',
          default=False, help=(
              u'Enable profiling of memory usage. Intended for '
              u'troubleshooting memory issues.'))

      argument_group.add_argument(
          '--profile_sample_rate', '--profile-sample-rate',
          dest='profile_sample_rate', action='store', default=0, help=(
              u'The profile sample rate (defaults to a sample every {0:d} '
              u'files).').format(self._DEFAULT_PROFILING_SAMPLE_RATE))

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ExtractionTool, self).ParseOptions(options)

    # TODO: refactor in sub parse functions.
    # TODO: make sure that only/all options defined in the add functions
    # are parsed.

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

    self._enable_profiling = getattr(options, u'enable_profiling', False)

    profile_sample_rate = getattr(options, u'profile_sample_rate', None)
    if profile_sample_rate:
      try:
        self._profiling_sample_rate = int(profile_sample_rate, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid profile sample rate: {0:s}.'.format(profile_sample_rate))

    serializer_format = getattr(
        options, u'serializer_format', definitions.SERIALIZER_FORMAT_PROTOBUF)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          u'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

    self._filter_expression = getattr(options, u'filter', None)
    if self._filter_expression:
      # TODO: refactor self._filter_object out the tool into the frontend.
      self._filter_object = pfilter.GetMatcher(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    filter_file = getattr(options, u'file_filter', None)
    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'No such collection filter file: {0:s}.'.format(filter_file))

    self._filter_file = filter_file

    self._debug_mode = getattr(options, u'debug', False)

    self._old_preprocess = getattr(options, u'old_preprocess', False)

    timezone_string = getattr(options, u'timezone', None)
    if timezone_string and timezone_string != u'list':
      self._timezone = pytz.timezone(timezone_string)

    self._single_process_mode = getattr(
        options, u'single_process', False)

    self._output_module = getattr(options, u'output_module', None)

    self._operating_system = getattr(options, u'os', None)
    self._process_archive_files = getattr(options, u'scan_archives', False)
    self._text_prepend = getattr(options, u'text_prepend', None)

    if self._operating_system:
      self._mount_path = getattr(options, u'filename', None)
