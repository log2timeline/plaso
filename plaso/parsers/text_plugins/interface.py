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


class PyparsingLineStructure(object):
  """Line structure.

  Attributes:
    expression (pyparsing.ParserElement): pyparsing expression to parse
        the line structure.
    name (str): name to identify the line structure.
    weight (int): number of times the line structure was successfully used.
  """

  def __init__(self, name, expression):
    """Initializes a line structure.

    Args:
      name (str): name to identify the line structure.
      expression (pyparsing.ParserElement): pyparsing expression to parse
          the line structure.
    """
    super(PyparsingLineStructure, self).__init__()
    self.expression = expression
    self.name = name
    self.weight = 0

  def ParseString(self, string):
    """Parses a string.

    Args:
      string (str): string to parse.

    Returns:
      tuple[pyparsing.ParseResults, int, int]: parsed tokens, start and end
          offset or None if the string could not be parsed.
    """
    try:
      structure_generator = self.expression.scanString(string, maxMatches=1)
      return next(structure_generator, None)

    except pyparsing.ParseException as exception:
      logger.debug('Unable to parse string with error: {0!s}'.format(exception))

    return None


class TextPlugin(plugins.BasePlugin):
  """The interface for text plugins."""

  NAME = 'text_plugin'
  DATA_FORMAT = 'Text file'

  ENCODING = None

  # The maximum line length of a single read.
  MAXIMUM_LINE_LENGTH = 400

  # List of tuples of pyparsing expression per unique identifier that define
  # the supported grammar.
  _LINE_STRUCTURES = []

  # The maximum number of consecutive lines that do not match the grammar before
  # aborting parsing.
  _MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  # TODO: remove after refactoring.
  _SINGLE_LINE_MODE = False

  def __init__(self):
    """Initializes a parser."""
    super(TextPlugin, self).__init__()
    self._current_offset = 0
    self._line_structures = []
    self._parser_mediator = None

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

  def _GetMatchingLineStructure(self, string):
    """Retrieves the first matching line structure.

    Args:
      string (str): string.

    Returns:
      tuple: containing:

        int: index of matching line structure in _line_structures;
        PyparsingLineStructure: matching line structure;
        tuple[pyparsing.ParseResults, int, int]: parsed tokens, start and end
            offset.
    """
    for index, line_structure in enumerate(self._line_structures):
      result_tuple = line_structure.ParseString(string)
      if result_tuple:
        # Only want to parse the structure if it starts at the beginning of
        # the string.
        if result_tuple[1] == 0:
          return index, line_structure, result_tuple

    return None, None, None

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

  def _ParseLines(self, parser_mediator, text_reader):
    """Parses lines of text using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.
    """
    # Set the offset to the beginning of the file.
    self._current_offset = 0

    try:
      text_reader.ReadLines()
      self._current_offset = text_reader.get_offset()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to read and decode log line at offset {0:d}'.format(
              self._current_offset))
      return

    consecutive_line_failures = 0

    while text_reader.lines:
      if parser_mediator.abort:
        break

      if not self._SINGLE_LINE_MODE:
        text = text_reader.lines
      else:
        text = text_reader.ReadLine()
        if not text:
          continue

      index, line_structure, result_tuple = self._GetMatchingLineStructure(text)

      if result_tuple:
        parsed_structure, _, end = result_tuple

        try:
          self._ParseLineStructure(
              parser_mediator, index, line_structure, parsed_structure)
          consecutive_line_failures = 0

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record: {0:s} with error: {1!s}'.format(
                  line_structure.name, exception))

        if not self._SINGLE_LINE_MODE:
          text_reader.SkipAhead(end)

      else:
        if self._SINGLE_LINE_MODE:
          line = text
        else:
          line = text_reader.ReadLine()

        if len(line) > 80:
          line = '{0:s}...'.format(line[:77])

        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line: {0:d} "{1:s}"'.format(
                text_reader.line_number, line))

        consecutive_line_failures += 1
        if (consecutive_line_failures >
            self._MAXIMUM_CONSECUTIVE_LINE_FAILURES):
          parser_mediator.ProduceExtractionWarning(
              'more than {0:d} consecutive failures to parse lines.'.format(
                  self._MAXIMUM_CONSECUTIVE_LINE_FAILURES))
          break

      try:
        text_reader.ReadLines()
        self._current_offset = text_reader.get_offset()
      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning(
            'unable to read and decode log line at offset {0:d}'.format(
                self._current_offset))
        break

  def _ParseLineStructure(
      self, parser_mediator, index, line_structure, parsed_structure):
    """Parses a line structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      index (int): index of the line structure in the run-time list of line
          structures.
      line_structure (PyparsingLineStructure): line structure.
      parsed_structure (pyparsing.ParseResults): tokens from a string parsed
          with pyparsing.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    # TODO: use a callback per line structure name.
    self._ParseRecord(parser_mediator, line_structure.name, parsed_structure)

    line_structure.weight += 1

    while index > 0:
      previous_weight = self._line_structures[index - 1].weight
      if line_structure.weight < previous_weight:
        break

      self._line_structures[index] = self._line_structures[index - 1]
      self._line_structures[index - 1] = line_structure
      index -= 1

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

  def _SetLineStructures(self, line_structures):
    """Sets the line structures.

    Args:
      line_structures ([(str, pyparsing.ParserElement)]): tuples of pyparsing
          expressions to parse a line and their names.
    """
    self._line_structures = []
    for key, expression in line_structures:
      # Using parseWithTabs() overrides Pyparsing's default replacement of tabs
      # with spaces to SkipAhead() the correct number of bytes after a match.
      expression.parseWithTabs()

      line_structure = PyparsingLineStructure(key, expression)
      self._line_structures.append(line_structure)

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
      file_object.seek(0, os.SEEK_SET)

      encoding = self.ENCODING or parser_mediator.codepage
      text_reader = text_parser.EncodedTextReader(
          file_object, buffer_size=self.MAXIMUM_LINE_LENGTH, encoding=encoding,
          encoding_errors='text_parser_handler')

      self._ParseLines(parser_mediator, text_reader)

    finally:
      self._parser_mediator = None
