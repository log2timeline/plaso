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
from plaso.lib import errors
from plaso.lib import py2to3

import pytz


class CLITool(object):
  """Class that implements a CLI tool.

  Attributes:
    list_timezones: boolean value to indicate the time zones should be listed.
    preferred_encoding: string containing the preferred encoding of single-byte
                        or multi-byte character strings (sometimes referred to
                        as extended ASCII).
  """

  # The maximum number of characters of a line written to the output writer.
  _LINE_LENGTH = 80

  # The fall back preferred encoding.
  _PREFERRED_ENCODING = u'utf-8'

  NAME = u''

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: optional input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: optional output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
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
    self._input_reader = input_reader
    self._log_file = None
    self._output_writer = output_writer
    self._quiet_mode = False
    self._timezone = pytz.UTC
    self._views_format_type = views.ViewsFactory.FORMAT_TYPE_CLI

    self.list_timezones = False
    self.preferred_encoding = preferred_encoding

  def _ConfigureLogging(
      self, filename=None, format_string=None, log_level=None):
    """Configure the logger.

    If a filename is specified and the corresponding log file already exists,
    the file is truncated.

    Args:
      filename: optional path to a filename to append logs to. Defaults to None,
                which means logs will not be redirected to a file.
      format_string: optional format string for the logs. Defaults to None,
                     which in turn configures the logger to use a default format
                     string.
      log_level: optional integer representing the log level, eg. logging.DEBUG.
                 Defaults to None, which configures the logger to use INFO
                 level.
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

  def _ParseDataLocationOption(self, options):
    """Parses the data location option.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    data_location = self.ParseStringOption(options, u'data_location')
    if not data_location:
      # Determine if we are running from the source directory.
      # This should get us the path to the "plaso/cli" directory.
      data_location = os.path.dirname(__file__)
      # In order to get to the main path of the egg file we need to traverse
      # two directories up.
      data_location = os.path.dirname(data_location)
      data_location = os.path.dirname(data_location)
      # There are two options: running from source or from an egg file.
      data_location_egg = os.path.join(data_location, u'share', u'plaso')
      data_location_source = os.path.join(data_location, u'data')

      if os.path.exists(data_location_egg):
        data_location = data_location_egg
      elif os.path.exists(data_location_source):
        data_location = data_location_source
      else:
        # Otherwise determine if there is shared plaso data location.
        data_location = os.path.join(sys.prefix, u'share', u'plaso')

        if not os.path.exists(data_location):
          data_location = None

    logging.info(
        u'Data files will be loaded from {0:s} by default.'.format(
            data_location))
    self._data_location = data_location

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    self._debug_mode = getattr(options, u'debug', False)
    self._quiet_mode = getattr(options, u'quiet', False)

    if self._debug_mode and self._quiet_mode:
      logging.warning(
          u'Cannot use debug and quiet mode at the same time, defaulting to '
          u'debug output.')

  def _ParseTimezoneOption(self, options):
    """Parses the timezone options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    timezone_string = self.ParseStringOption(options, u'timezone')
    if isinstance(timezone_string, basestring):
      if timezone_string.lower() == u'list':
        self.list_timezones = True

      elif timezone_string:
        try:
          self._timezone = pytz.timezone(timezone_string)
        except pytz.UnknownTimeZoneError:
          raise errors.BadConfigOption(
              u'Unknown timezone: {0:s}'.format(timezone_string))

  def AddBasicOptions(self, argument_group):
    """Adds the basic options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    version_string = u'plaso - {0:s} version {1:s}'.format(
        self.NAME, plaso.GetVersion())

    # We want a custom help message and not the default argparse one.
    argument_group.add_argument(
        u'-h', u'--help', action=u'help',
        help=u'show this help message and exit.')

    argument_group.add_argument(
        u'-V', u'--version', dest=u'version', action=u'version',
        version=version_string, help=u'show the version information.')

  def AddDataLocationOption(self, argument_group):
    """Adds the data location option to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--data', action=u'store', dest=u'data_location', type=str,
        metavar=u'PATH', default=None, help=u'the location of the data files.')

  def AddInformationalOptions(self, argument_group):
    """Adds the informational options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
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
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--logfile', u'--log_file', u'--log-file', action=u'store',
        metavar=u'FILENAME', dest=u'log_file', type=str, default=u'', help=(
            u'If defined all log messages will be redirected to this file '
            u'instead the default STDERR.'))

  def AddTimezoneOption(self, argument_group):
    """Adds the timezone option to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'-z', u'--zone', u'--timezone', dest=u'timezone', action=u'store',
        type=str, default=u'UTC', help=(
            u'explicitly define the timezone. Typically the timezone is '
            u'determined automatically where possible. Use "-z list" to '
            u'see a list of available timezones.'))

  def ListTimeZones(self):
    """Lists the timezones."""
    max_length = 0
    for timezone_name in pytz.all_timezones:
      if len(timezone_name) > max_length:
        max_length = len(timezone_name)

    utc_date_time = datetime.datetime.utcnow()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Zones')
    table_view.AddColumnNames([u'Timezone', u'UTC Offset'])
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

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    self._ParseInformationalOptions(options)

  def ParseLogFileOptions(self, options):
    """Parses the log file options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    self._log_file = self.ParseStringOption(options, u'log_file')

  def ParseStringOption(self, options, argument_name):
    """Parses a specific string command line argument.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      argument_nmae: the name of the command line argument.

    Returns:
      A string containing the command line argument value or None.

    Raises:
      BadConfigOption: if the command line argument value cannot be converted
                       to a Unicode string.
    """
    argument_value = getattr(options, argument_name, None)
    if not argument_value:
      return

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
  """Class that implements the CLI input reader interface."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      encoding: optional input encoding. The default is "utf-8".
    """
    super(CLIInputReader, self).__init__()
    self._encoding = encoding

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """


class CLIOutputWriter(object):
  """Class that implements the CLI output writer interface."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding: optional output encoding. The default is "utf-8".
    """
    super(CLIOutputWriter, self).__init__()
    self._encoding = encoding

  @abc.abstractmethod
  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """


class FileObjectInputReader(CLIInputReader):
  """Class that implements a file-like object input reader.

  This input reader relies on the file-like object having a readline method.
  """

  def __init__(self, file_object, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      file_object: the file-like object to read from.
      encoding: optional input encoding. The default is "utf-8".
    """
    super(FileObjectInputReader, self).__init__(encoding=encoding)
    self._errors = u'strict'
    self._file_object = file_object

  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
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
  """Class that implements a stdin input reader."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the input reader object.

    Args:
      encoding: optional input encoding. The default is "utf-8".
    """
    super(StdinInputReader, self).__init__(sys.stdin, encoding=encoding)


class FileObjectOutputWriter(CLIOutputWriter):
  """Class that implements a file-like object output writer.

  This output writer relies on the file-like object having a write method.
  """

  def __init__(self, file_object, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      file_object: the file-like object to write to.
      encoding: optional output encoding. The default is "utf-8".
    """
    super(FileObjectOutputWriter, self).__init__(encoding=encoding)
    self._errors = u'strict'
    self._file_object = file_object

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
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
  """Class that implements a stdout output writer."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding: optional output encoding. The default is "utf-8".
    """
    super(StdoutOutputWriter, self).__init__(sys.stdout, encoding=encoding)
