# -*- coding: utf-8 -*-
"""This file contains the interface for text plugins."""

import abc
import codecs
import os

import pyparsing

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins
from plaso.parsers import text_parser


class TextPlugin(plugins.BasePlugin):
  """The interface for text plugins."""

  NAME = 'text_plugin'
  DATA_FORMAT = 'Text file'

  ENCODING = None

  # List of tuples of pyparsing expression per unique identifier that define
  # the supported grammar.
  _LINE_STRUCTURES = []

  # PyParsing grammer used to verify the text-log file format. Note that since
  # this is called often it should optimize on failing fast.
  VERIFICATION_GRAMMAR = None
  VERIFICATION_LITERALS = None

  # The maximum number of consecutive lines that do not match the grammar before
  # aborting parsing.
  _MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  def __init__(self):
    """Initializes a parser."""
    super(TextPlugin, self).__init__()
    self._current_offset = 0
    self._parser_mediator = None
    self._pyparsing_grammar = None

    codecs.register_error('text_parser_handler', self._EncodingErrorHandler)

    self._SetLineStructures(self._LINE_STRUCTURES)

  def _EncodingErrorHandler(self, exception):
    """Encoding error handler.

    Args:
      exception [UnicodeDecodeError]: exception.

    Returns:
      tuple[str, int]: replacement string and a position where encoding should
          continue.

    Raises:
      TypeError: if exception is not of type UnicodeDecodeError.
    """
    if not isinstance(exception, UnicodeDecodeError):
      raise TypeError('Unsupported exception type.')

    if self._parser_mediator:
      self._parser_mediator.ProduceExtractionWarning(
          'error decoding 0x{0:02x} at offset: {1:d}'.format(
              exception.object[exception.start],
              self._current_offset + exception.start))

    escaped = '\\x{0:2x}'.format(exception.object[exception.start])
    return escaped, exception.start + 1

  def _GetDecimalValueFromStructure(self, structure, name):
    """Retrieves a decimal integer value from a Pyparsing structure.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.

    Returns:
      int: decimal integer value or None if not available or invalid.
    """
    integer_value = self._GetValueFromStructure(structure, name)

    try:
      return int(integer_value, 10)
    except (TypeError, ValueError):
      pass

    return None

  def _GetStringValueFromStructure(self, structure, name):
    """Retrieves a string value from a Pyparsing structure.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.

    Returns:
      str: string value or None if not available or empty.
    """
    string_value = self._GetValueFromStructure(
        structure, name, default_value='')
    return string_value.strip() or None

  def _GetValueFromStructure(self, structure, name, default_value=None):
    """Retrieves a token value from a Pyparsing structure.

    This method ensures the token value is set to the default value when
    the token is not present in the structure. Instead of returning
    the Pyparsing default value of an empty byte stream (b'').

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.
      default_value (Optional[object]): default value.

    Returns:
      object: value in the token or default value if the token is not available
          in the structure.
    """
    value = structure.get(name, default_value)
    if isinstance(value, pyparsing.ParseResults) and not value:
      # Ensure the return value is not an empty pyparsing.ParseResults otherwise
      # serialization will fail.
      return None

    return value

  def _ParseFinalize(self, parser_mediator):  # pylint: disable=unused-argument
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    return

  def _ParseHeader(self, parser_mediator, text_reader):  # pylint: disable=unused-argument
    """Parses a text-log file header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    return

  def _ParseLines(self, parser_mediator, text_reader):
    """Parses lines of text using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.
    """
    consecutive_line_failures = 0

    try:
      text_reader.ReadLines()
      self._current_offset = text_reader.get_offset()
    except UnicodeDecodeError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read and decode log line at offset {0:d} with error: '
          '{1!s}').format(self._current_offset, exception))
      return

    while text_reader.lines:
      if parser_mediator.abort:
        break

      if consecutive_line_failures > self._MAXIMUM_CONSECUTIVE_LINE_FAILURES:
        parser_mediator.ProduceExtractionWarning(
            'more than {0:d} consecutive failures to parse lines.'.format(
                self._MAXIMUM_CONSECUTIVE_LINE_FAILURES))
        break

      try:
        key, structure, _, end = self._ParseString(text_reader.lines)

      except errors.ParseError as exception:
        line = text_reader.ReadLine()
        # Pyparsing does not appear to detect single empty lines hence that
        # we ignore them here.
        if not line:
          continue

        logger.debug('unable to parse string with error: {0!s}'.format(
            exception))

        if len(line) > 80:
          line = '{0:s}...'.format(line[:77])

        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line: {0:d} "{1:s}"'.format(
                text_reader.line_number, line))

        consecutive_line_failures += 1

        continue

      consecutive_line_failures = 0

      try:
        # TODO: use a callback per key.
        self._ParseRecord(parser_mediator, key, structure)

      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse record: {0:s} with error: {1!s}'.format(
                key, exception))

      text_reader.SkipAhead(end)

      try:
        text_reader.ReadLines()
        self._current_offset = text_reader.get_offset()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read and decode log line at offset {0:d} with error: '
            '{1!s}').format(self._current_offset, exception))
        break

  @abc.abstractmethod
  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """

  def _ParseString(self, string):
    """Parses a string for known grammar.

    Args:
      string (str): string.

    Returns:
      tuple[str, pyparsing.ParseResults, int, int]: key, parsed tokens, start
          and end offset.

    Raises:
      ParseError: when the string cannot be parsed by the grammar.
    """
    try:
      structure_generator = self._pyparsing_grammar.scanString(
          string, maxMatches=1)
      structure, start, end = next(structure_generator)

    except StopIteration:
      structure = None

    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure:
      raise errors.ParseError('No match found.')

    if start > 0 and '\n' in string[:start + 1]:
      raise errors.ParseError('Found a line preceeding match.')

    # Unwrap the line structure and retrieve its name (key).
    keys = list(structure.keys())
    if len(keys) != 1:
      raise errors.ParseError('Missing key of line structructure.')

    return keys[0], structure[0], start, end

  def _SetLineStructures(self, line_structures):
    """Sets the line structures.

    Args:
      line_structures ([(str, pyparsing.ParserElement)]): tuples of pyparsing
          expressions to parse a line and their names.
    """
    self._pyparsing_grammar = None

    for key, expression in line_structures:
      # Wrap the line structures in groups with a result name to build a single
      # pyparsing grammar.
      if not isinstance(expression, pyparsing.Group):
        expression = pyparsing.Group(expression).setResultsName(key)

      if not self._pyparsing_grammar:
        self._pyparsing_grammar = expression
      else:
        self._pyparsing_grammar ^= expression

    # Override Pyparsing's default replacement of tabs with spaces to
    # SkipAhead() the correct number of bytes after a match.
    self._pyparsing_grammar.parseWithTabs()

    # Override Pyparsing's whitespace characters to spaces only.
    self._pyparsing_grammar.setDefaultWhitespaceChars(' ')

  def _VerifyString(self, string):
    """Checks a string for known grammar.

    Args:
      string (str): string.

    Returns:
      pyparsing.ParseResults: parsed tokens.

    Raises:
      ParseError: when the string cannot be parsed by the grammar.
    """
    try:
      structure = self.VERIFICATION_GRAMMAR.parseString(string)
    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure:
      raise errors.ParseError('No match found.')

    return structure

  @abc.abstractmethod
  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, file_object=None, **kwargs):
    """Extracts events from a text log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (Optional[dfvfs.FileIO]): a file-like object.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(TextPlugin, self).Process(parser_mediator)

    # Keep a reference to the parser mediator for the encoding error handler.
    self._parser_mediator = parser_mediator

    try:
      # Set the offset to the beginning of the file.
      file_object.seek(0, os.SEEK_SET)
      self._current_offset = 0

      encoding = self.ENCODING
      if not encoding:
        encoding = parser_mediator.GetCodePage()

      text_reader = text_parser.EncodedTextReader(
          file_object, encoding=encoding, encoding_errors='text_parser_handler')

      try:
        text_reader.ReadLines()
        self._current_offset = text_reader.get_offset()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read and decode log line at offset {0:d} with error: '
            '{1!s}').format(self._current_offset, exception))
        return

      try:
        self._ParseHeader(parser_mediator, text_reader)
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parser header with error: {0!s}').format(exception))
        return

      self._ParseLines(parser_mediator, text_reader)

      self._ParseFinalize(parser_mediator)

    finally:
      self._parser_mediator = None
