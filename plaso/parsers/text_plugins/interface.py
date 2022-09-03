# -*- coding: utf-8 -*-
"""This file contains the interface for text plugins."""

import abc
import codecs
import os

import pyparsing

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins


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
      pyparsing.ParseResults: parsed tokens or None if the string could not
          be parsed.
    """
    try:
      return self.expression.parseString(string)
    except pyparsing.ParseException as exception:
      logger.debug('Unable to parse string with error: {0!s}'.format(
          exception))

    return None


class TextPlugin(plugins.BasePlugin):
  """The interface for text plugins."""

  NAME = 'text_plugin'
  DATA_FORMAT = 'Text file'

  _ENCODING = None

  _EMPTY_LINES = frozenset(['\n', '\r', '\r\n'])

  # List of tuples of pyparsing expression per unique identifier that define
  # the supported grammar.
  _LINE_STRUCTURES = []

  # The maximum number of consecutive lines that do not match the grammar before
  # aborting parsing.
  _MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  # Allow for a maximum of 40 empty lines before we bail out.
  _MAXIMUM_NUMBER_OF_EMPTY_LINES = 40

  # The maximum line length of a single read.
  _MAXIMUM_LINE_LENGTH = 400

  def __init__(self):
    """Initializes a parser."""
    super(TextPlugin, self).__init__()
    self._current_offset = 0
    self._line_structures = []
    self._parser_mediator = None

    codecs.register_error('text_parser_handler', self._EncodingErrorHandler)

    for key, expression in self._LINE_STRUCTURES:
      line_structure = PyparsingLineStructure(key, expression)
      self._line_structures.append(line_structure)

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
    return (escaped, exception.start + 1)

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

  def _ReadLine(self, text_file_object, max_len=None, depth=0):
    """Reads a line from a text file.

    Args:
      text_file_object (dfvfs.TextFile): text file.
      max_len (Optional[int]): maximum number of bytes a single line can take,
          where None means all remaining bytes should be read.
      depth (Optional[int]): number of new lines the parser encountered.

    Returns:
      str: single line read from the file-like object, or the maximum number of
          characters, if max_len defined and line longer than the defined size.

    Raises:
      UnicodeDecodeError: if the text cannot be decoded using the specified
          encoding and encoding errors is set to strict.
    """
    line = text_file_object.readline(size=max_len)

    if not line:
      return ''

    if line in self._EMPTY_LINES:
      if depth == self._MAXIMUM_NUMBER_OF_EMPTY_LINES:
        return ''

      return self._ReadLine(text_file_object, max_len=max_len, depth=depth + 1)

    return line

  def _ParseLines(self, parser_mediator, text_file_object):
    """Parses lines of text using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    line = self._ReadLine(text_file_object, max_len=self._MAXIMUM_LINE_LENGTH)

    consecutive_line_failures = 0
    # Set the offset to the beginning of the file.
    self._current_offset = 0
    # Read every line in the text file.
    while line:
      if parser_mediator.abort:
        break

      index = None
      line_structure = None
      parsed_structure = None

      # Try to parse the line using all the line structures.
      for index, line_structure in enumerate(self._line_structures):
        parsed_structure = line_structure.ParseString(line)
        if parsed_structure:
          break

      if parsed_structure:
        try:
          self._ParseLineStructure(
              parser_mediator, index, line_structure, parsed_structure)
          consecutive_line_failures = 0

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record: {0:s} with error: {1!s}'.format(
                  line_structure.name, exception))

      else:
        if len(line) > 80:
          line = '{0:s}...'.format(line[:77])

        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line: "{0:s}" at offset: {1:d}'.format(
                line, self._current_offset))

        consecutive_line_failures += 1
        if (consecutive_line_failures >
            self._MAXIMUM_CONSECUTIVE_LINE_FAILURES):
          raise errors.WrongParser(
              'more than {0:d} consecutive failures to parse lines.'.format(
                  self._MAXIMUM_CONSECUTIVE_LINE_FAILURES))

      self._current_offset = text_file_object.get_offset()

      try:
        line = self._ReadLine(
            text_file_object, max_len=self._MAXIMUM_LINE_LENGTH)
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
    self._ParseRecord(parser_mediator, line_structure.name, parsed_structure)

    line_structure.weight += 1

    if index:
      previous_weight = self._line_structures[index - 1].weight
      if previous_weight and line_structure.weight > previous_weight:
        self._line_structures[index] = self._line_structures[index - 1]
        self._line_structures[index - 1] = line_structure

  @abc.abstractmethod
  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """

  @abc.abstractmethod
  def CheckRequiredFormat(self, lines):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      lines (list[str]): lines from the text file.

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

      text_file_object = text_file.TextFile(
          file_object, encoding=self._ENCODING or parser_mediator.codepage,
          encoding_errors='text_parser_handler')

      self._current_offset = 0
      self._ParseLines(parser_mediator, text_file_object)

    finally:
      self._parser_mediator = None
