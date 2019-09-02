# -*- coding: utf-8 -*-
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing file-like objects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

from __future__ import unicode_literals

import abc

import pyparsing

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.parsers import interface
from plaso.parsers import logger


# Pylint complains about some functions not being implemented that shouldn't
# be since they need to be implemented by children.
# pylint: disable=abstract-method


# TODO: determine if this method should be merged with PyParseIntCast.

# pylint: disable=unused-argument
def ConvertTokenToInteger(string, location, tokens):
  """Pyparsing parse action callback to convert a token into an integer value.

  Args:
    string (str): original string.
    location (int): location in the string where the token was found.
    tokens (list[str]): tokens.

  Returns:
    int: integer value or None.
  """
  try:
    return int(tokens[0], 10)
  except ValueError:
    pass


def PyParseRangeCheck(lower_bound, upper_bound):
  """Verify that a number is within a defined range.

  This is a callback method for pyparsing setParseAction
  that verifies that a read number is within a certain range.

  To use this method it needs to be defined as a callback method
  in setParseAction with the upper and lower bound set as parameters.

  Args:
    lower_bound (int): lower bound of the range.
    upper_bound (int): upper bound of the range.

  Returns:
    Function: callback method that can be used by pyparsing setParseAction.
  """
  # pylint: disable=unused-argument
  def CheckRange(string, location, tokens):
    """Parse the arguments.

    Args:
      string (str): original string.
      location (int): location in the string where the match was made
      tokens (list[str]): tokens.
    """
    try:
      check_number = tokens[0]
    except IndexError:
      check_number = -1

    if check_number < lower_bound:
      raise pyparsing.ParseException(
          'Value: {0:d} precedes lower bound: {1:d}'.format(
              check_number, lower_bound))

    if check_number > upper_bound:
      raise pyparsing.ParseException(
          'Value: {0:d} exceeds upper bound: {1:d}'.format(
              check_number, upper_bound))

  # Since callback methods for pyparsing need to accept certain parameters
  # and there is no way to define conditions, like upper and lower bounds
  # we need to return here a method that accepts those pyparsing parameters.
  return CheckRange


def PyParseIntCast(string, location, tokens):
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


def PyParseJoinList(string, location, tokens):
  """Return a joined token from a list of tokens.

  This is a callback method for pyparsing setParseAction that modifies
  the returned token list to join all the elements in the list to a single
  token.

  Args:
    string (str): original string.
    location (int): location in the string where the match was made.
    tokens (list[str]): extracted tokens, where the string to be converted
        is stored.
  """
  join_list = []
  for token in tokens:
    try:
      join_list.append(str(token))
    except UnicodeDecodeError:
      join_list.append(repr(token))

  tokens[0] = ''.join(join_list)
  del tokens[1:]


class PyparsingConstants(object):
  """Constants for pyparsing-based parsers."""

  # Numbers.
  INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(PyParseIntCast)

  IPV4_ADDRESS = pyparsing.pyparsing_common.ipv4_address
  IPV6_ADDRESS = pyparsing.pyparsing_common.ipv6_address
  IP_ADDRESS = (IPV4_ADDRESS | IPV6_ADDRESS)

  # TODO: deprecate and remove, use THREE_LETTERS instead.
  # TODO: fix Python 3 compatibility of .uppercase and .lowercase.
  # pylint: disable=no-member
  MONTH = pyparsing.Word(
      pyparsing.string.ascii_uppercase, pyparsing.string.ascii_lowercase,
      exact=3)

  # Define date structures.
  HYPHEN = pyparsing.Literal('-').suppress()

  ONE_OR_TWO_DIGITS = pyparsing.Word(
      pyparsing.nums, min=1, max=2).setParseAction(PyParseIntCast)
  TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      PyParseIntCast)
  THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      PyParseIntCast)
  FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      PyParseIntCast)

  THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  DATE_ELEMENTS = (
      FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      TWO_DIGITS.setResultsName('day_of_month'))
  TIME_ELEMENTS = (
      TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      TWO_DIGITS.setResultsName('seconds'))
  TIME_MSEC_ELEMENTS = (
      TIME_ELEMENTS + pyparsing.Word('.,', exact=1).suppress() +
      INTEGER.setResultsName('microseconds'))

  # Date structures defined as a single group.
  DATE = pyparsing.Group(DATE_ELEMENTS)
  DATE_TIME = pyparsing.Group(DATE_ELEMENTS + TIME_ELEMENTS)
  DATE_TIME_MSEC = pyparsing.Group(DATE_ELEMENTS + TIME_MSEC_ELEMENTS)
  TIME = pyparsing.Group(TIME_ELEMENTS)

  TIME_MSEC = TIME + pyparsing.Suppress('.') + INTEGER
  # TODO: replace by
  # TIME_MSEC = pyparsing.Group(TIME_MSEC_ELEMENTS)

  COMMENT_LINE_HASH = pyparsing.Literal('#') + pyparsing.SkipTo(
      pyparsing.LineEnd())
  # TODO: Add more commonly used structs that can be used by parsers.
  PID = pyparsing.Word(
      pyparsing.nums, min=1, max=5).setParseAction(PyParseIntCast)


class PyparsingSingleLineTextParser(interface.FileObjectParser):
  """Single line text parser interface based on pyparsing."""

  # The actual structure, this needs to be defined by each parser.
  # This is defined as a list of tuples so that more then a single line
  # structure can be defined. That way the parser can support more than a
  # single type of log entry, despite them all having in common the constraint
  # that each log entry is a single line.
  # The tuple should have two entries, a key and a structure. This is done to
  # keep the structures in an order of priority/preference.
  # The key is a comment or an identification that is passed to the ParseRecord
  # function so that the developer can identify which structure got parsed.
  # The value is the actual pyparsing structure.
  LINE_STRUCTURES = []

  # In order for the tool to not read too much data into a buffer to evaluate
  # whether or not the parser is the right one for this file or not we
  # specifically define a maximum amount of bytes a single line can occupy. This
  # constant can be overwritten by implementations if their format might have a
  # longer line than 400 bytes.
  MAX_LINE_LENGTH = 400

  # The maximum number of consecutive lines that don't match known line
  # structures to encounter before aborting parsing.
  MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  _ENCODING = None

  _EMPTY_LINES = frozenset(['\n', '\r', '\r\n'])

  # Allow for a maximum of 40 empty lines before we bail out.
  _MAXIMUM_DEPTH = 40

  def __init__(self):
    """Initializes a parser."""
    super(PyparsingSingleLineTextParser, self).__init__()
    self._current_offset = 0
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures = list(self.LINE_STRUCTURES)

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
    return structure.get(name, default_value)

  # Pylint is confused by the formatting of the bytes_in argument.
  # pylint: disable=missing-param-doc,missing-type-doc
  def _IsText(self, bytes_in, encoding=None):
    """Examine the bytes in and determine if they are indicative of text.

    Parsers need quick and at least semi reliable method of discovering whether
    or not a particular byte stream is text or resembles text or not. This can
    be used in text parsers to determine if a file is a text file or not for
    instance.

    The method assumes the byte sequence is either ASCII, UTF-8, UTF-16 or
    method supplied character encoding. Otherwise it will make the assumption
    the byte sequence is not text, but a byte sequence.

    Args:
      bytes_in (bytes|str): byte stream to examine.
      encoding (Optional[str]): encoding to test, if not defined ASCII and
          UTF-8 are tried.

    Returns:
      bool: True if the bytes stream contains text.
    """
    # TODO: Improve speed and accuracy of this method.
    # Start with the assumption we are dealing with text.
    is_text = True

    if isinstance(bytes_in, py2to3.UNICODE_TYPE):
      return is_text

    # Check if this is ASCII text string.
    for value in bytes_in:
      if py2to3.PY_2:
        value = ord(value)
      if not 31 < value < 128:
        is_text = False
        break

    # We have an ASCII string.
    if is_text:
      return is_text

    # Check if this is UTF-8
    try:
      bytes_in.decode('utf-8')
      return True

    except UnicodeDecodeError:
      pass

    if encoding:
      try:
        bytes_in.decode(encoding)
        return True

      except LookupError:
        logger.error('Unsupported encoding: {0:s}'.format(encoding))
      except UnicodeDecodeError:
        pass

    return False

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
          encoding.
    """
    line = text_file_object.readline(size=max_len)

    if not line:
      return ''

    if line in self._EMPTY_LINES:
      if depth == self._MAXIMUM_DEPTH:
        return ''

      return self._ReadLine(text_file_object, max_len=max_len, depth=depth + 1)

    return line

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text file-like object using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    if not self._line_structures:
      raise errors.UnableToParseFile(
          'Line structure undeclared, unable to proceed.')

    encoding = self._ENCODING or parser_mediator.codepage
    text_file_object = text_file.TextFile(file_object, encoding=encoding)

    try:
      line = self._ReadLine(text_file_object, max_len=self.MAX_LINE_LENGTH)
    except UnicodeDecodeError:
      raise errors.UnableToParseFile(
          'Not a text file or encoding not supported.')

    if not line:
      raise errors.UnableToParseFile('Not a text file.')

    if len(line) == self.MAX_LINE_LENGTH or len(
        line) == self.MAX_LINE_LENGTH - 1:
      logger.debug((
          'Trying to read a line and reached the maximum allowed length of '
          '{0:d}. The last few bytes of the line are: {1:s} [parser '
          '{2:s}]').format(
              self.MAX_LINE_LENGTH, repr(line[-10:]), self.NAME))

    if not self._IsText(line):
      raise errors.UnableToParseFile('Not a text file, unable to proceed.')

    if not self.VerifyStructure(parser_mediator, line):
      raise errors.UnableToParseFile('Wrong file structure.')

    consecutive_line_failures = 0
    index = None
    # Set the offset to the beginning of the file.
    self._current_offset = 0
    # Read every line in the text file.
    while line:
      if parser_mediator.abort:
        break
      parsed_structure = None
      use_key = None
      # Try to parse the line using all the line structures.
      for index, (key, structure) in enumerate(self._line_structures):
        try:
          parsed_structure = structure.parseString(line)
        except pyparsing.ParseException:
          pass
        if parsed_structure:
          use_key = key
          break

      if parsed_structure:
        self.ParseRecord(parser_mediator, use_key, parsed_structure)
        consecutive_line_failures = 0
        if index is not None and index != 0:
          key_structure = self._line_structures.pop(index)
          self._line_structures.insert(0, key_structure)
      else:
        if len(line) > 80:
          line = '{0:s}...'.format(line[:77])
        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line: "{0:s}" at offset: {1:d}'.format(
                line, self._current_offset))
        consecutive_line_failures += 1
        if (consecutive_line_failures >
            self.MAXIMUM_CONSECUTIVE_LINE_FAILURES):
          raise errors.UnableToParseFile(
              'more than {0:d} consecutive failures to parse lines.'.format(
                  self.MAXIMUM_CONSECUTIVE_LINE_FAILURES))

      self._current_offset = text_file_object.get_offset()

      try:
        line = self._ReadLine(text_file_object, max_len=self.MAX_LINE_LENGTH)
      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning(
            'unable to read and decode log line at offset {0:d}'.format(
                self._current_offset))
        break

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def VerifyStructure(self, parser_mediator, line):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): single line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """


class EncodedTextReader(object):
  """Encoded text reader."""

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


class PyparsingMultiLineTextParser(PyparsingSingleLineTextParser):
  """Multi line text parser interface based on pyparsing."""

  BUFFER_SIZE = 2048

  def __init__(self):
    """Initializes a parser object."""
    super(PyparsingMultiLineTextParser, self).__init__()
    self._buffer_size = self.BUFFER_SIZE

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text file-like object using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not self.LINE_STRUCTURES:
      raise errors.UnableToParseFile('Missing line structures.')

    encoding = self._ENCODING or parser_mediator.codepage
    text_reader = EncodedTextReader(
        encoding, buffer_size=self.BUFFER_SIZE)

    text_reader.Reset()

    try:
      text_reader.ReadLines(file_object)
    except UnicodeDecodeError as exception:
      raise errors.UnableToParseFile(
          'Not a text file, with error: {0!s}'.format(exception))

    if not self.VerifyStructure(parser_mediator, text_reader.lines):
      raise errors.UnableToParseFile('Wrong file structure.')

    # Using parseWithTabs() overrides Pyparsing's default replacement of tabs
    # with spaces to SkipAhead() the correct number of bytes after a match.
    for key, structure in self.LINE_STRUCTURES:
      structure.parseWithTabs()


    consecutive_line_failures = 0
    # Read every line in the text file.
    while text_reader.lines:
      if parser_mediator.abort:
        break

      # Initialize pyparsing objects.
      tokens = None
      start = 0
      end = 0

      key = None

      index = None

      # Try to parse the line using all the line structures.
      for index, (key, structure) in enumerate(self._line_structures):
        try:
          structure_generator = structure.scanString(
              text_reader.lines, maxMatches=1)
          parsed_structure = next(structure_generator, None)
        except pyparsing.ParseException:
          parsed_structure = None

        if not parsed_structure:
          continue

        tokens, start, end = parsed_structure

        # Only want to parse the structure if it starts
        # at the beginning of the buffer.
        if start == 0:
          break

      if tokens and start == 0:
        # Move matching key, structure pair to the front of the list, so that
        # structures that are more likely to match are tried first.
        if index is not None and index != 0:
          key_structure = self._line_structures.pop(index)
          self._line_structures.insert(0, key_structure)

        try:
          self.ParseRecord(parser_mediator, key, tokens)
          consecutive_line_failures = 0
        except (errors.ParseError, errors.TimestampError) as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record: {0:s} with error: {1!s}'.format(
                  key, exception))

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
            raise errors.UnableToParseFile(
                'more than {0:d} consecutive failures to parse lines.'.format(
                    self.MAXIMUM_CONSECUTIVE_LINE_FAILURES))
      try:
        text_reader.ReadLines(file_object)
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read lines with error: {0!s}'.format(exception))

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Returns:
      EventObject: event or None.
    """

  # pylint: disable=arguments-differ,redundant-returns-doc
  @abc.abstractmethod
  def VerifyStructure(self, parser_mediator, lines):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
