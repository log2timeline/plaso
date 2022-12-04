# -*- coding: utf-8 -*-
"""Text log parser."""

import codecs
import os

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


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
    current_offset = self._file_object.get_offset()

    decoded_data = self._stream_reader.read(size=self._buffer_size)
    if decoded_data:
      # Remove a byte-order mark at the start of the file.
      if current_offset == 0 and decoded_data[0] == '\ufeff':
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
  """Text-based log file parser."""

  NAME = 'text'
  DATA_FORMAT = 'text-based log file'

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
    for plugin_name, plugin in self._plugins_per_name.items():
      if parser_mediator.abort:
        break

      file_object.seek(0, os.SEEK_SET)

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
            '{1!s}').format(plugin_name, exception))
        continue

      if hasattr(plugin, 'GetYearLessLogHelper'):
        year_less_log_helper = plugin.GetYearLessLogHelper()
        parser_mediator.AddYearLessLogHelper(year_less_log_helper)


manager.ParsersManager.RegisterParser(TextLogParser)
