# -*- coding: utf-8 -*-
"""The CLI tools classes."""

import abc
import locale
import logging
import sys

import plaso


class CLITool(object):
  """Class that implements a CLI tool."""

  # The maximum number of characters of a line written to the output writer.
  _LINE_LENGTH = 80

  # The fall back preferred encoding.
  _PREFERRED_ENCODING = u'utf-8'

  NAME = u''

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
    super(CLITool, self).__init__()

    preferred_encoding = locale.getpreferredencoding()
    if not preferred_encoding:
      preferred_encoding = self._PREFERRED_ENCODING

    if not input_reader:
      input_reader = StdinInputReader(encoding=preferred_encoding)
    if not output_writer:
      output_writer = StdoutOutputWriter(encoding=preferred_encoding)

    self._input_reader = input_reader
    self._output_writer = output_writer

    self.preferred_encoding = preferred_encoding

  def AddBasicOptions(self, argument_group):
    """Adds the basic options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    version_string = u'plaso - {0:s} version {1:s}'.format(
        self.NAME, plaso.GetVersion())

    argument_group.add_argument(
        u'-h', u'--help', action=u'help', help=(
            u'Show this help message and exit.'))

    argument_group.add_argument(
        u'-V', u'--version', dest=u'version', action=u'version',
        version=version_string, help=u'Show the current version.')

  def ParseOptions(self, unused_options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    return

  def PrintColumnValue(self, name, description, column_width=25):
    """Prints a value with a name and description aligned to the column width.

    Args:
      name: the name.
      description: the description.
      column_width: optional column width. The default is 25.
    """
    line_length = self._LINE_LENGTH - column_width - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(column_width)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        column_width + 3)

    if len(description) < line_length:
      self._output_writer.Write(primary_format_string.format(name, description))
      return

    # Split the description in words.
    words = description.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= line_length:
        current = len(word)
        lines.append(u' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(u' '.join(word_buffer))

    # Print the column value on multiple lines.
    self._output_writer.Write(primary_format_string.format(name, lines[0]))
    for line in lines[1:]:
      self._output_writer.Write(secondary_format_string.format(u'', line))

  def PrintHeader(self, text, character=u'*'):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.
    """
    self._output_writer.Write(u'\n')

    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(character, self._LINE_LENGTH)
    header_string = format_string.format(u' {0:s} '.format(text))
    self._output_writer.Write(header_string)

  def PrintSeparatorLine(self):
    """Prints a separator line."""
    self._output_writer.Write(u'{0:s}\n'.format(u'-' * self._LINE_LENGTH))


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
