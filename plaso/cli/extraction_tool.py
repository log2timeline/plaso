# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import

# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import

from plaso.cli import storage_media_tool
from plaso.lib import errors


class ExtractionTool(storage_media_tool.StorageMediaTool):
  """Extraction CLI tool."""

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes an CLI tool.

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
    self._mount_path = None
    self._operating_system = None
    self._preferred_year = None
    self._process_archives = False
    self._process_compressed_streams = True
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False

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
