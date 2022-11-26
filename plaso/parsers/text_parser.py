# -*- coding: utf-8 -*-
"""Text log parser."""

import codecs

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


# TODO: determine if this method should be merged with PyParseIntCast.

def ConvertTokenToInteger(string, location, tokens):  # pylint: disable=unused-argument
  """Pyparsing parse action callback to convert a token into an integer value.

  Args:
    string (str): original string.
    location (int): location in the string where the token was found.
    tokens (list[str]): tokens.

  Returns:
    int: integer value or None.
  """
  try:
    integer = int(tokens[0], 10)
  except ValueError:
    integer = None

  return integer


def PyParseIntCast(string, location, tokens):  # pylint: disable=unused-argument
  """Return an integer from a string.

  This is a pyparsing callback method that converts the matched
  string into an integer.

  The method modifies the content of the tokens list and converts
  them all to an integer value.

  Args:
    string (str): original string.
    location (int): location in the string where the match was made.
    tokens (list[str]): extracted tokens, where the string to be converted
        is stored.
  """
  # Cast the regular tokens.
  for index, token in enumerate(tokens):
    try:
      tokens[index] = int(token)
    except ValueError:
      logger.error('Unable to cast [{0:s}] to an int, setting to 0'.format(
          token))
      tokens[index] = 0

  # We also need to cast the dictionary built tokens.
  for key in tokens.keys():
    try:
      tokens[key] = int(tokens[key], 10)
    except ValueError:
      logger.error(
          'Unable to cast [{0:s} = {1:d}] to an int, setting to 0'.format(
              key, tokens[key]))
      tokens[key] = 0


class EncodedTextReader(object):
  """Encoded text reader.

  Attributes:
    lines (str): lines of text.
  """

  def __init__(
      self, file_object, buffer_size=2048, encoding='utf-8',
      encoding_errors='strict'):
    """Initializes the encoded text reader object.

    Args:
      file_object (FileIO): a file-like object to read from.
      buffer_size (Optional[int]): buffer size.
      encoding (Optional[str]): text encoding.
      encoding_errors (Optional[str]): text encoding errors handler.
    """
    stream_reader_class = codecs.getreader(encoding)

    super(EncodedTextReader, self).__init__()
    self._buffer_size = buffer_size
    self._file_object = file_object
    self._stream_reader = stream_reader_class(
        file_object, errors=encoding_errors)

    self.lines = ''
    self.line_number = 0

  def ReadLine(self):
    """Reads a line.

    Returns:
      str: line read from the lines buffer.
    """
    if not self.lines:
      self.ReadLines()

    line, _, self.lines = self.lines.partition('\n')
    self.line_number += 1

    return line

  def ReadLines(self):
    """Reads lines into the lines buffer."""
    while len(self.lines) < self._buffer_size:
      current_offset = self._file_object.get_offset()

      decoded_data = self._stream_reader.read(size=self._buffer_size)
      if not decoded_data:
        break

      # Remove a byte-order mark at the start of the file.
      if current_offset == 0 and decoded_data and decoded_data[0] == '\ufeff':
        decoded_data = decoded_data[1:]

      # Strip carriage returns from the text.
      decoded_data = '\n'.join([
          line.rstrip('\r') for line in decoded_data.split('\n')])

      self.lines = ''.join([self.lines, decoded_data])

  def SkipAhead(self, number_of_characters):
    """Skips ahead a number of characters.

    Args:
      number_of_characters (int): number of characters.
    """
    lines_size = len(self.lines)
    while number_of_characters >= lines_size:
      number_of_characters -= lines_size

      self.lines = ''
      self.ReadLines()
      lines_size = len(self.lines)
      if lines_size == 0:
        return

    self.line_number += self.lines[:number_of_characters].count('\n')
    self.lines = self.lines[number_of_characters:]

  # Note: that the following functions do not follow the style guide
  # because they are part of the file-like object interface.
  # pylint: disable=invalid-name

  def get_offset(self):
    """Retrieves the current offset into the file-like object.

    Returns:
      int: current offset into the file-like object.
    """
    return self._file_object.get_offset()


class TextLogParser(interface.FileObjectParser):
  """Text log parser."""

  NAME = 'text'
  DATA_FORMAT = 'Text log file'

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    for plugin in self._plugins:
      if parser_mediator.abort:
        break

      encoding = plugin.ENCODING or parser_mediator.codepage
      text_reader = EncodedTextReader(
          file_object, buffer_size=plugin.MAXIMUM_LINE_LENGTH,
          encoding=encoding)

      # TODO: only read lines once for a specific encoding.
      try:
        text_reader.ReadLines()
      except UnicodeDecodeError as exception:
        raise errors.WrongParser(
            'Unable to read lines with error: {0!s}'.format(exception))

      if not plugin.CheckRequiredFormat(parser_mediator, text_reader):
        continue

      try:
        plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)
      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse text file with error: '
            '{1!s}').format(plugin.NAME, exception))
        continue

      if hasattr(plugin, 'GetYearLessLogHelper'):
        year_less_log_helper = plugin.GetYearLessLogHelper()
        parser_mediator.AddYearLessLogHelper(year_less_log_helper)


manager.ParsersManager.RegisterParser(TextLogParser)
