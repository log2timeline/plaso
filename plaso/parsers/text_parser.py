# -*- coding: utf-8 -*-
"""Base parser for text formats."""

import abc
import codecs

import pyparsing

from dfvfs.helpers import text_file

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


class SingleLineTextParser(interface.FileObjectParser):
  """Single-line text parser."""

  NAME = 'text'
  DATA_FORMAT = 'Single-line text log file'

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text file-like object using a pyparsing definition.

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

      text_file_object = text_file.TextFile(
          file_object, encoding=plugin.ENCODING or parser_mediator.codepage)

      if not plugin.CheckRequiredFormat(parser_mediator, text_file_object):
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


class EncodedTextReader(object):
  """Encoded text reader.

  Attributes:
    lines (str): lines of text.
  """

  def __init__(self, encoding, buffer_size=2048):
    """Initializes the encoded text reader object.

    Args:
      encoding (str): encoding.
      buffer_size (Optional[int]): buffer size.
    """
    super(EncodedTextReader, self).__init__()
    self._buffer = ''
    self._buffer_size = buffer_size
    self._current_offset = 0
    self._encoding = encoding

    self.lines = ''

  def _ReadLine(self, file_object):
    """Reads a line from the file object.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      str: line read from the file-like object.
    """
    if len(self._buffer) < self._buffer_size:
      content = file_object.read(self._buffer_size)
      content = content.decode(self._encoding)
      self._buffer = ''.join([self._buffer, content])

    line, new_line, self._buffer = self._buffer.partition('\n')
    if not line and not new_line:
      line = self._buffer
      self._buffer = ''

    self._current_offset += len(line)

    # Strip carriage returns from the text.
    if line.endswith('\r'):
      line = line[:-len('\r')]

    if new_line:
      line = ''.join([line, '\n'])
      self._current_offset += len('\n')

    return line

  def ReadLine(self, file_object):
    """Reads a line.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      str: line read from the lines buffer.
    """
    line, _, self.lines = self.lines.partition('\n')
    if not line:
      self.ReadLines(file_object)
      line, _, self.lines = self.lines.partition('\n')

    return line

  def ReadLines(self, file_object):
    """Reads lines into the lines buffer.

    Args:
      file_object (dfvfs.FileIO): file-like object.
    """
    lines_size = len(self.lines)
    if lines_size < self._buffer_size:
      lines_size = self._buffer_size - lines_size
      while lines_size > 0:
        line = self._ReadLine(file_object)
        if not line:
          break

        self.lines = ''.join([self.lines, line])
        lines_size -= len(line)

  def Reset(self):
    """Resets the encoded text reader."""
    self._buffer = ''
    self._current_offset = 0
    self.lines = ''

  def SkipAhead(self, file_object, number_of_characters):
    """Skips ahead a number of characters.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      number_of_characters (int): number of characters.
    """
    lines_size = len(self.lines)
    while number_of_characters >= lines_size:
      number_of_characters -= lines_size

      self.lines = ''
      self.ReadLines(file_object)
      lines_size = len(self.lines)
      if lines_size == 0:
        return

    self.lines = self.lines[number_of_characters:]


class PyparsingMultiLineTextParser(interface.FileObjectParser):
  """Multi-line text parser interface based on pyparsing."""

  BUFFER_SIZE = 2048

  # The actual structure, this needs to be defined by each parser.
  # This is defined as a list of tuples so that more than a single line
  # structure can be defined. That way the parser can support more than a
  # single type of log entry, despite them all having in common the constraint
  # that each log entry is a single line.
  # The tuple should have two entries, a key and a structure. This is done to
  # keep the structures in an order of priority/preference.
  # The key is a comment or an identification that is passed to the ParseRecord
  # function so that the developer can identify which structure got parsed.
  # The value is the actual pyparsing structure.
  LINE_STRUCTURES = []

  # The maximum number of consecutive lines that don't match known line
  # structures to encounter before aborting parsing.
  MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  _ENCODING = None

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  def __init__(self):
    """Initializes a parser."""
    super(PyparsingMultiLineTextParser, self).__init__()
    self._buffer_size = self.BUFFER_SIZE
    self._current_offset = 0
    self._line_structures = []
    self._parser_mediator = None

    codecs.register_error('text_parser_handler', self._EncodingErrorHandler)

    if self.LINE_STRUCTURES:
      self._SetLineStructures(self.LINE_STRUCTURES)

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
    self.ParseRecord(parser_mediator, line_structure.name, parsed_structure)

    line_structure.weight += 1

    if index:
      previous_weight = self._line_structures[index - 1].weight
      if previous_weight and line_structure.weight > previous_weight:
        self._line_structures[index] = self._line_structures[index - 1]
        self._line_structures[index - 1] = line_structure

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

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text file-like object using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    if not self._line_structures:
      raise errors.WrongParser('Missing line structures.')

    self._parser_mediator = parser_mediator

    encoding = self._ENCODING or parser_mediator.codepage
    text_reader = EncodedTextReader(
        encoding, buffer_size=self.BUFFER_SIZE)

    text_reader.Reset()

    try:
      text_reader.ReadLines(file_object)
    except UnicodeDecodeError as exception:
      raise errors.WrongParser(
          'Not a text file, with error: {0!s}'.format(exception))

    if not self.VerifyStructure(parser_mediator, text_reader.lines):
      raise errors.WrongParser('Wrong file structure.')

    consecutive_line_failures = 0
    # Read every line in the text file.
    while text_reader.lines:
      if parser_mediator.abort:
        break

      # Initialize pyparsing objects.
      tokens = None
      start = 0
      end = 0

      index = None
      line_structure = None

      # Try to parse the line using all the line structures.
      for index, line_structure in enumerate(self._line_structures):
        try:
          structure_generator = line_structure.expression.scanString(
              text_reader.lines, maxMatches=1)
          parsed_structure = next(structure_generator, None)
        except pyparsing.ParseException:
          parsed_structure = None

        if parsed_structure:
          tokens, start, end = parsed_structure

          # Only want to parse the structure if it starts
          # at the beginning of the buffer.
          if start == 0:
            break

      if tokens and start == 0:
        try:
          self._ParseLineStructure(
              parser_mediator, index, line_structure, tokens)
          consecutive_line_failures = 0

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record: {0:s} with error: {1!s}'.format(
                  line_structure.name, exception))

        text_reader.SkipAhead(file_object, end)

      else:
        odd_line = text_reader.ReadLine(file_object)
        if odd_line:
          if len(odd_line) > 80:
            odd_line = '{0:s}...'.format(odd_line[:77])

          parser_mediator.ProduceExtractionWarning(
              'unable to parse log line: {0:s}'.format(repr(odd_line)))

          consecutive_line_failures += 1
          if (consecutive_line_failures >
              self.MAXIMUM_CONSECUTIVE_LINE_FAILURES):
            raise errors.WrongParser(
                'more than {0:d} consecutive failures to parse lines.'.format(
                    self.MAXIMUM_CONSECUTIVE_LINE_FAILURES))

      try:
        text_reader.ReadLines(file_object)
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read lines with error: {0!s}'.format(exception))

    if hasattr(self, 'GetYearLessLogHelper'):
      year_less_log_helper = self.GetYearLessLogHelper()
      parser_mediator.AddYearLessLogHelper(year_less_log_helper)

  @abc.abstractmethod
  def ParseRecord(self, parser_mediator, key, structure):
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
  def VerifyStructure(self, parser_mediator, lines):  # pylint: disable=arguments-renamed
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """


manager.ParsersManager.RegisterParser(SingleLineTextParser)
