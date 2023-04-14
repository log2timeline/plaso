# -*- coding: utf-8 -*-
"""Text log parser."""

import codecs
import io
import os

import pysigscan

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class EncodedTextReader(object):
  """Encoded text reader.

  Attributes:
    line_number (int): current line number.
    lines (str): lines of text.
    lines_size (int): size of the lines of text.
  """

  BUFFER_SIZE = 65536

  _READ_BUFFER_SIZE = 16 * BUFFER_SIZE

  def __init__(
      self, file_object, encoding='utf-8', encoding_errors='strict'):
    """Initializes the encoded text reader object.

    Args:
      file_object (FileIO): a file-like object to read from.
      encoding (Optional[str]): text encoding.
      encoding_errors (Optional[str]): text encoding errors handler.
    """
    stream_reader_class = codecs.getreader(encoding)

    super(EncodedTextReader, self).__init__()
    self._file_object = file_object
    self._stream_reader = stream_reader_class(
        file_object, errors=encoding_errors)

    self.line_number = 0
    self.lines = ''
    self.lines_size = 0

  def ReadLine(self):
    """Reads a line.

    Returns:
      str: line read from the lines buffer.
    """
    if not self.lines:
      self.ReadLines()

    line, _, self.lines = self.lines.partition('\n')
    self.lines_size += len(line) + 1
    self.line_number += 1

    return line

  def ReadLines(self):
    """Reads lines into the lines buffer."""
    if self.lines_size < self.BUFFER_SIZE:
      current_offset = self._file_object.tell()

      # Consequative reads, decodes and joins are expensive hence we read
      # a larger buffer at once.
      decoded_data = self._stream_reader.read(size=self._READ_BUFFER_SIZE)
      if decoded_data:
        # Remove a byte-order mark at the start of the file.
        if current_offset == 0 and decoded_data[0] == '\ufeff':
          decoded_data = decoded_data[1:]

        # Strip carriage returns from the text.
        decoded_data = '\n'.join([
            line.rstrip('\r') for line in decoded_data.split('\n')])

        self.lines = ''.join([self.lines, decoded_data])
        self.lines_size += len(decoded_data)

  def SkipAhead(self, number_of_characters):
    """Skips ahead a number of characters.

    Args:
      number_of_characters (int): number of characters.
    """
    while number_of_characters >= self.lines_size:
      number_of_characters -= self.lines_size

      self.lines = ''
      self.lines_size = 0

      self.ReadLines()

      if self.lines_size == 0:
        return

    self.line_number += self.lines[:number_of_characters].count('\n')
    self.lines = self.lines[number_of_characters:]
    self.lines_size -= number_of_characters

  # Note: that the following functions do not follow the style guide
  # because they are part of the file-like object interface.
  # pylint: disable=invalid-name

  def get_offset(self):
    """Retrieves the current offset into the file-like object.

    Returns:
      int: current offset into the file-like object.
    """
    return self._file_object.tell()


class TextLogParser(interface.FileObjectParser):
  """Text-based log file parser."""

  NAME = 'text'
  DATA_FORMAT = 'text-based log file'

  _NON_TEXT_CHARACTERS = frozenset([
      '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x0b', '\x0e',
      '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17',
      '\x18', '\x19', '\x1a', '\x1c', '\x1d', '\x1e', '\x1f', '\x7f'])

  _plugin_classes = {}

  def __init__(self):
    """Initializes a text-based log parser."""
    super(TextLogParser, self).__init__()
    self._plugins_per_encoding = {}
    self._format_scanner = None
    self._non_sigscan_plugin_names = None
    self._plugin_name_per_format_identifier = {}

  def _ContainsBinary(self, text):
    """Determines if the text contains binary (non-text) characters.

    Args:
      text (str): text.

    Returns:
      bool: True if the text contains binary (non-text) characters.
    """
    return bool(self._NON_TEXT_CHARACTERS.intersection(set(text)))

  def _CreateFormatScanner(self, parser_mediator):
    """Creates a signature scanner for required format check.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._non_sigscan_plugin_names = set()
    self._plugin_name_per_format_identifier = {}

    scanner_object = pysigscan.scanner()
    scanner_object.set_scan_buffer_size(65536)

    for plugin_name, plugin in self._plugins_per_name.items():
      if not plugin.VERIFICATION_LITERALS:
        self._non_sigscan_plugin_names.add(plugin_name)
      else:
        encoding = plugin.ENCODING
        if not encoding:
          encoding = parser_mediator.GetCodePage()

        for index, literal in enumerate(plugin.VERIFICATION_LITERALS):
          identifier = '{0:s}{1:d}'.format(plugin_name, index)
          encoded_literal = literal.encode(encoding)
          scanner_object.add_signature(
              identifier, 0, encoded_literal,
              pysigscan.signature_flags.NO_OFFSET)

          self._plugin_name_per_format_identifier[identifier] = plugin_name

    if self._plugin_name_per_format_identifier:
      self._format_scanner = scanner_object

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes (set[str]): names of the plugins to enable, where
          set(['*']) represents all plugins. Note the default plugin, if
          it exists, is always enabled and cannot be disabled.
    """
    self._plugins_per_name = {}
    self._plugins_per_encoding = {}
    if not self._plugin_classes:
      return

    for plugin_name, plugin_class in self._plugin_classes.items():
      if plugin_name == self._default_plugin_name:
        self._default_plugin = plugin_class()
        continue

      if (plugin_includes != self.ALL_PLUGINS and
          plugin_name not in plugin_includes):
        continue

      plugin_object = plugin_class()
      self._plugins_per_name[plugin_name] = plugin_object

      encoding = plugin_class.ENCODING or 'default'
      if encoding not in self._plugins_per_encoding:
        self._plugins_per_encoding[encoding] = []

      self._plugins_per_encoding[encoding].append(plugin_object)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    if not self._format_scanner and not self._non_sigscan_plugin_names:
      self._CreateFormatScanner(parser_mediator)

    file_object.seek(0, os.SEEK_SET)

    # Cache the first 64k of encoded data so it does not need to be read for
    # each encoding.
    encoded_data_buffer = file_object.read(EncodedTextReader.BUFFER_SIZE)
    encoded_data_file_object = io.BytesIO(encoded_data_buffer)

    plugins_with_matching_literals = set()
    if self._format_scanner:
      parser_mediator.SampleFormatCheckStartTiming('text_format_scanner')

      try:
        scan_state = pysigscan.scan_state()
        self._format_scanner.scan_file_object(
            scan_state, encoded_data_file_object)

        for scan_result in iter(scan_state.scan_results):
          plugin_name = self._plugin_name_per_format_identifier.get(
              scan_result.identifier, None)

          plugins_with_matching_literals.add(plugin_name)

      finally:
        parser_mediator.SampleFormatCheckStopTiming('text_format_scanner')

    matching_plugin = False
    for encoding, plugins in self._plugins_per_encoding.items():
      if parser_mediator.abort:
        break

      if encoding == 'default':
        encoding = parser_mediator.GetCodePage()

      text_reader = None

      for plugin in plugins:
        if parser_mediator.abort:
          break

        profiling_name = '/'.join([self.NAME, plugin.NAME])

        parser_mediator.SampleFormatCheckStartTiming(profiling_name)

        try:
          logger.debug(
              'Checking required format of: {0:s} in encoding: {1:s}'.format(
                  plugin.NAME, encoding))

          result = False
          if (plugin.NAME in plugins_with_matching_literals or
              plugin.NAME in self._non_sigscan_plugin_names):
            if not text_reader:
              encoded_data_file_object.seek(0, os.SEEK_SET)
              text_reader = EncodedTextReader(
                  encoded_data_file_object, encoding=encoding)

              text_reader.ReadLines()

              # TODO: check if this works with xchatscrollback log.
              if self._ContainsBinary(text_reader.lines):
                logger.debug('Detected binary format')
                continue

            result = plugin.CheckRequiredFormat(parser_mediator, text_reader)

        except UnicodeDecodeError:
          logger.debug(
              'Unable to read text-based log file with encoding: {0:s}'.format(
                  encoding))
          result = False

        finally:
          parser_mediator.SampleFormatCheckStopTiming(profiling_name)

        if result:
          matching_plugin = True

          parser_mediator.SampleStartTiming(profiling_name)

          try:
            plugin.UpdateChainAndProcess(
                parser_mediator, file_object=file_object)
          except Exception as exception:  # pylint: disable=broad-except
            parser_mediator.ProduceExtractionWarning((
                'plugin: {0:s} unable to parse text file with error: '
                '{1!s}').format(plugin.NAME, exception))
            continue

          finally:
            parser_mediator.SampleStopTiming(profiling_name)

          if hasattr(plugin, 'GetYearLessLogHelper'):
            year_less_log_helper = plugin.GetYearLessLogHelper()
            parser_mediator.AddYearLessLogHelper(year_less_log_helper)

          break

      if matching_plugin:
        break

    if not matching_plugin:
      raise errors.WrongParser('No matching text-based log plugin found.')


manager.ParsersManager.RegisterParser(TextLogParser)
