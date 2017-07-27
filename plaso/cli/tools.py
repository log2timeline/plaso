# -*- coding: utf-8 -*-
"""The CLI tools classes."""

import abc
import datetime
import locale
import logging
import os
import sys

import plaso

from plaso.cli import views
from plaso.engine import engine
from plaso.lib import errors
from plaso.lib import py2to3

import pytz  # pylint: disable=wrong-import-order


class CLITool(object):
  """CLI tool.

  Attributes:
    list_profilers (bool): True if the profilers should be listed.
    list_timezones (bool): True if the time zones should be listed.
    preferred_encoding (str): preferred encoding of single-byte or multi-byte
        character strings, sometimes referred to as extended ASCII.
  """
  # The maximum number of characters of a line written to the output writer.
  _LINE_LENGTH = 80

  # The fall back preferred encoding.
  _PREFERRED_ENCODING = u'utf-8'

  _PROFILERS_INFORMATION = {
      u'parsers': u'Profile CPU time per parser',
      u'processing': u'Profile CPU time of processing phases',
      u'serializers': u'Profile CPU time of serialization'}

  if engine.BaseEngine.SupportsGuppyMemoryProfiling():
    _PROFILERS_INFORMATION[u'guppy'] = (
        u'Profile memory usage per process using guppy')

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  NAME = u''

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(CLITool, self).__init__()

    preferred_encoding = locale.getpreferredencoding()
    if not preferred_encoding:
      preferred_encoding = self._PREFERRED_ENCODING

    if not input_reader:
      input_reader = StdinInputReader(encoding=preferred_encoding)
    if not output_writer:
      output_writer = StdoutOutputWriter(encoding=preferred_encoding)

    self._data_location = None
    self._debug_mode = False
    self._encode_errors = u'strict'
    self._input_reader = input_reader
    self._log_file = None
    self._output_writer = output_writer
    self._preferred_time_zone = None
    self._profilers = set()
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._quiet_mode = False
    self._views_format_type = views.ViewsFactory.FORMAT_TYPE_CLI

    self.list_profilers = False
    self.list_timezones = False
    self.preferred_encoding = preferred_encoding

  def _ConfigureLogging(
      self, filename=None, format_string=None, log_level=None):
    """Configure the logger.

    If a filename is specified and the corresponding log file already exists,
    the file is truncated.

    Args:
      filename (Optional[str]): path to a filename to append logs to, where
          None means logs will not be redirected to a file.
      format_string (Optional[str]): format string for the logs, where None
           configures the logger to use a default format string.
      log_level (Optional[int]): integer representing the log level, for
          example logging.DEBUG, where None represents logging.INFO.
    """
    # Remove all possible log handlers.
    for handler in logging.root.handlers:
      logging.root.removeHandler(handler)

    if log_level is None:
      log_level = logging.INFO

    if not format_string:
      format_string = u'[%(levelname)s] %(message)s'

    if filename:
      logging.basicConfig(
          level=log_level, format=format_string, filename=filename,
          filemode=u'w')
    else:
      logging.basicConfig(level=log_level, format=format_string)

  def _EncodeString(self, string):
    """Encodes a string in the preferred encoding.

    Returns:
      bytes: encoded string.
    """
    try:
      # Note that encode() will first convert string into a Unicode string
      # if necessary.
      encoded_string = string.encode(
          self.preferred_encoding, errors=self._encode_errors)
    except UnicodeEncodeError:
      if self._encode_errors == u'strict':
        logging.error(
            u'Unable to properly write output due to encoding error. '
            u'Switching to error tolerant encoding which can result in '
            u'non Basic Latin (C0) characters to be replaced with "?" or '
            u'"\\ufffd".')
        self._encode_errors = u'replace'

      encoded_string = string.encode(
          self.preferred_encoding, errors=self._encode_errors)

    return encoded_string

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    self._debug_mode = getattr(options, u'debug', False)
    self._quiet_mode = getattr(options, u'quiet', False)

    if self._debug_mode and self._quiet_mode:
      logging.warning(
          u'Cannot use debug and quiet mode at the same time, defaulting to '
          u'debug output.')

  def _ParseLogFileOptions(self, options):
    """Parses the log file options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    self._log_file = self.ParseStringOption(options, u'log_file')

  def _ParseProfilingOptions(self, options):
    """Parses the profiling options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    profilers_string = self.ParseStringOption(options, u'profilers')
    if isinstance(profilers_string, py2to3.STRING_TYPES):
      if profilers_string.lower() == u'list':
        self.list_profilers = True

      elif profilers_string:
        profilers = set(profilers_string.split(u','))

        supported_profilers = set(self._PROFILERS_INFORMATION.keys())
        unsupported_profilers = profilers.difference(supported_profilers)
        if unsupported_profilers:
          unsupported_profilers = u', '.join(unsupported_profilers)
          raise errors.BadConfigOption(
              u'Unsupported profilers: {0:s}'.format(unsupported_profilers))

        self._profilers = profilers

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

  def _ParseTimezoneOption(self, options):
    """Parses the timezone options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    time_zone_string = self.ParseStringOption(options, u'timezone')
    if isinstance(time_zone_string, py2to3.STRING_TYPES):
      if time_zone_string.lower() == u'list':
        self.list_timezones = True

      elif time_zone_string:
        try:
          pytz.timezone(time_zone_string)
        except pytz.UnknownTimeZoneError:
          raise errors.BadConfigOption(
              u'Unknown time zone: {0:s}'.format(time_zone_string))

        self._preferred_time_zone = time_zone_string

  def _PromptUserForInput(self, input_text):
    """Prompts user for an input.

    Args:
      input_text (str): text used for prompting the user for input.

    Returns:
      str: input read from the user.
    """
    self._output_writer.Write(u'{0:s}: '.format(input_text))
    return self._input_reader.Read()

  def AddBasicOptions(self, argument_group):
    """Adds the basic options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    version_string = u'plaso - {0:s} version {1:s}'.format(
        self.NAME, plaso.__version__)

    # We want a custom help message and not the default argparse one.
    argument_group.add_argument(
        u'-h', u'--help', action=u'help',
        help=u'show this help message and exit.')

    argument_group.add_argument(
        u'-V', u'--version', dest=u'version', action=u'version',
        version=version_string, help=u'show the version information.')

  def AddInformationalOptions(self, argument_group):
    """Adds the informational options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '-d', '--debug', dest='debug', action='store_true', default=False,
        help=u'enable debug output.')

    argument_group.add_argument(
        '-q', '--quiet', dest='quiet', action='store_true', default=False,
        help=u'disable informational output.')

  def AddLogFileOptions(self, argument_group):
    """Adds the log file option to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--logfile', u'--log_file', u'--log-file', action=u'store',
        metavar=u'FILENAME', dest=u'log_file', type=str, default=u'', help=(
            u'If defined all log messages will be redirected to this file '
            u'instead the default STDERR.'))

  def AddProfilingOptions(self, argument_group):
    """Adds the profiling options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--profilers', dest=u'profilers', type=str, action=u'store',
        default=u'', metavar=u'PROFILERS_LIST', help=(
            u'Define a list of profilers to use by the tool. This is a comma '
            u'separated list where each entry is the name of a profiler. '
            u'Use "--profilers list" to list the available profilers.'))

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

  def AddTimeZoneOption(self, argument_group):
    """Adds the time zone option to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'-z', u'--zone', u'--timezone', dest=u'timezone', action=u'store',
        type=str, default=u'UTC', help=(
            u'explicitly define the timezone. Typically the timezone is '
            u'determined automatically where possible. Use "-z list" to '
            u'see a list of available timezones.'))

  def GetCommandLineArguments(self):
    """Retrieves the command line arguments.

    Returns:
      str: command line arguments.
    """
    command_line_arguments = sys.argv
    if not command_line_arguments:
      return u''

    if isinstance(command_line_arguments[0], py2to3.BYTES_TYPE):
      encoding = sys.stdin.encoding

      # Note that sys.stdin.encoding can be None.
      if not encoding:
        encoding = self.preferred_encoding

      try:
        command_line_arguments = [
            argument.decode(encoding) for argument in command_line_arguments]

      except UnicodeDecodeError:
        logging.error(
            u'Unable to properly read command line input due to encoding '
            u'error. Replacing non Basic Latin (C0) characters with "?" or '
            u'"\\ufffd".')

        command_line_arguments = [
            argument.decode(encoding, errors=u'replace')
            for argument in command_line_arguments]

    return u' '.join(command_line_arguments)

  def ListProfilers(self):
    """Lists information about the available profilers."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Profilers')

    for name, description in sorted(self._PROFILERS_INFORMATION.items()):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ListTimeZones(self):
    """Lists the timezones."""
    max_length = 0
    for timezone_name in pytz.all_timezones:
      if len(timezone_name) > max_length:
        max_length = len(timezone_name)

    utc_date_time = datetime.datetime.utcnow()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Timezone', u'UTC Offset'],
        title=u'Zones')
    for timezone_name in pytz.all_timezones:
      local_timezone = pytz.timezone(timezone_name)

      local_date_string = u'{0!s}'.format(
          local_timezone.localize(utc_date_time))
      if u'+' in local_date_string:
        _, _, diff = local_date_string.rpartition(u'+')
        diff_string = u'+{0:s}'.format(diff)
      else:
        _, _, diff = local_date_string.rpartition(u'-')
        diff_string = u'-{0:s}'.format(diff)

      table_view.AddRow([timezone_name, diff_string])

    table_view.Write(self._output_writer)

  def ParseNumericOption(self, options, name, base=10, default_value=None):
    """Parses a numeric option.

    If the option is not set the default value is returned.

    Args:
      options (argparse.Namespace): command line arguments.
      name (str): name of the numeric option.
      base (Optional[int]): base of the numeric value.
      default_value (Optional[object]): default value.

    Returns:
      int: numeric value.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    numeric_value = getattr(options, name, None)
    if not numeric_value:
      return default_value

    try:
      return int(numeric_value, base)

    except (TypeError, ValueError):
      name = name.replace(u'_', u' ')
      raise errors.BadConfigOption(
          u'Unsupported numeric value {0:s}: {1!s}.'.format(
              name, numeric_value))

  def ParseStringOption(self, options, argument_name, default_value=None):
    """Parses a string command line argument.

    Args:
      options (argparse.Namespace): command line arguments.
      argument_name (str): name of the command line argument.
      default_value (Optional[object]): default value of the command line
          argument.

    Returns:
      object: command line argument value. If the command line argument is
          not set the default value will be returned.

    Raises:
      BadConfigOption: if the command line argument value cannot be converted
          to a Unicode string.
    """
    argument_value = getattr(options, argument_name, None)
    if not argument_value:
      return default_value

    if isinstance(argument_value, py2to3.BYTES_TYPE):
      encoding = sys.stdin.encoding

      # Note that sys.stdin.encoding can be None.
      if not encoding:
        encoding = self.preferred_encoding

      try:
        argument_value = argument_value.decode(encoding)
      except UnicodeDecodeError as exception:
        raise errors.BadConfigOption((
            u'Unable to convert option: {0:s} to Unicode with error: '
            u'{1:s}.').format(argument_name, exception))

    elif not isinstance(argument_value, py2to3.UNICODE_TYPE):
      raise errors.BadConfigOption(
          u'Unsupported option: {0:s} string type required.'.format(
              argument_name))

    return argument_value

  def PrintSeparatorLine(self):
    """Prints a separator line."""
    self._output_writer.Write(u'-' * self._LINE_LENGTH)
    self._output_writer.Write(u'\n')


class CLIInputReader(object):
  """CLI input reader interface."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      encoding (Optional[str]): input encoding.
    """
    super(CLIInputReader, self).__init__()
    self._encoding = encoding

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      str: input.
    """


class CLIOutputWriter(object):
  """CLI output writer interface."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding (Optional[str]): output encoding.
    """
    super(CLIOutputWriter, self).__init__()
    self._encoding = encoding

  @abc.abstractmethod
  def Write(self, string):
    """Writes a string to the output.

    Args:
      string (str): output.
    """


class FileObjectInputReader(CLIInputReader):
  """File-like object input reader.

  This input reader relies on the file-like object having a readline method.
  """

  def __init__(self, file_object, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      file_object (file): file-like object to read from.
      encoding (Optional[str]): input encoding.
    """
    super(FileObjectInputReader, self).__init__(encoding=encoding)
    self._errors = u'strict'
    self._file_object = file_object

  def Read(self):
    """Reads a string from the input.

    Returns:
      str: input.
    """
    encoded_string = self._file_object.readline()

    try:
      string = encoded_string.decode(self._encoding, errors=self._errors)
    except UnicodeDecodeError:
      if self._errors == u'strict':
        logging.error(
            u'Unable to properly read input due to encoding error. '
            u'Switching to error tolerant encoding which can result in '
            u'non Basic Latin (C0) characters to be replaced with "?" or '
            u'"\\ufffd".')
        self._errors = u'replace'

      string = encoded_string.decode(self._encoding, errors=self._errors)

    return string


class StdinInputReader(FileObjectInputReader):
  """Stdin input reader."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      encoding (Optional[str]): input encoding.
    """
    super(StdinInputReader, self).__init__(sys.stdin, encoding=encoding)


class FileObjectOutputWriter(CLIOutputWriter):
  """File-like object output writer.

  This output writer relies on the file-like object having a write method.
  """

  def __init__(self, file_object, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      file_object (file): file-like object to read from.
      encoding (Optional[str]): output encoding.
    """
    super(FileObjectOutputWriter, self).__init__(encoding=encoding)
    self._errors = u'strict'
    self._file_object = file_object

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string (str): output.
    """
    try:
      # Note that encode() will first convert string into a Unicode string
      # if necessary.
      encoded_string = string.encode(self._encoding, errors=self._errors)
    except UnicodeEncodeError:
      if self._errors == u'strict':
        logging.error(
            u'Unable to properly write output due to encoding error. '
            u'Switching to error tolerant encoding which can result in '
            u'non Basic Latin (C0) characters to be replaced with "?" or '
            u'"\\ufffd".')
        self._errors = u'replace'

      encoded_string = string.encode(self._encoding, errors=self._errors)

    self._file_object.write(encoded_string)


class StdoutOutputWriter(FileObjectOutputWriter):
  """Stdout output writer."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding (Optional[str]): output encoding.
    """
    super(StdoutOutputWriter, self).__init__(sys.stdout, encoding=encoding)
