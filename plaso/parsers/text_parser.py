# -*- coding: utf-8 -*-
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing fileobjects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

import abc
import csv
import logging

import pyparsing

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import utils
from plaso.parsers import interface


# Pylint complains about some functions not being implemented that shouldn't
# be since they need to be implemented by children.
# pylint: disable=abstract-method

class TextCSVParser(interface.FileObjectParser):
  """An implementation of a simple CSV line-per-entry log files.

  Attributes:
    encoding (str): encoding used in the CSV file, or None if the encoding is
        unknown.
  """

  # A list that contains the names of all the fields in the log file.
  COLUMNS = []

  # A CSV file is comma separated, but this can be overwritten to include
  # tab, pipe or other character separation. Note this must be a byte string
  # otherwise TypeError: "delimiter" must be an 1-character string is raised.
  VALUE_SEPARATOR = b','

  # If there is a header before the lines start it can be defined here, and
  # the number of header lines that need to be skipped before the parsing
  # starts.
  NUMBER_OF_HEADER_LINES = 0

  # If there is a special quote character used inside the structured text
  # it can be defined here.
  QUOTE_CHAR = b'"'

  # Value that should not appear inside the file, made to test the actual
  # file to see if it confirms to standards.
  MAGIC_TEST_STRING = b'RegnThvotturMeistarans'

  def __init__(self, encoding=None):
    """Initializes a parser object.

    Args:
      encoding (Optional[str]): encoding used in the CSV file, where None
          indicates the codepage of the parser mediator should be used.
    """
    super(TextCSVParser, self).__init__()
    self.encoding = encoding

  def _ConvertRowToUnicode(self, parser_mediator, row):
    """Converts all strings in a CSV row dict to Unicode.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, bytes]): a row from a CSV file, where the dictionary
          key contains the column name and the value a binary string.

    Returns:
      dict[str, str]: a row from the CSV file, where the dictionary key
          contains the column name and the value a Unicode string.
    """
    if not self.encoding:
      # If no encoding is set, we default to the system codepage.
      self.encoding = parser_mediator.codepage

    for key, value in iter(row.items()):
      try:
        row[key] = value.decode(self.encoding)
      except UnicodeDecodeError:
        replaced_value = value.decode(self.encoding, errors=u'replace')
        parser_mediator.ProduceExtractionError(
            u'error decoding string as {0:s}, characters have been '
            u'replaced in {1:s}'.format(self.encoding, replaced_value))
        row[key] = replaced_value
    return row

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parse a line of the log file and extract event objects.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset: the offset of the row.
      row: a dictionary containing all the fields as denoted in the
           COLUMNS class list. Strings in this dict are Unicode strings.
    """
    # TODO: replace EventObject with a CSV specific event object.
    event_object = events.EventObject()
    if row_offset is not None:
      event_object.offset = row_offset
    event_object.row_dict = row
    parser_mediator.ProduceEvent(event_object)

  def ParseFileObject(self, parser_mediator, file_object, **unused_kwargs):
    """Parses a CSV text file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    path_spec_printable = file_entry.path_spec.comparable.replace(u'\n', u';')

    text_file_object = text_file.TextFile(file_object)

    # If we specifically define a number of lines we should skip, do that here.
    for _ in range(0, self.NUMBER_OF_HEADER_LINES):
      _ = text_file_object.readline()

    reader = csv.DictReader(
        text_file_object, fieldnames=self.COLUMNS,
        restkey=self.MAGIC_TEST_STRING, restval=self.MAGIC_TEST_STRING,
        delimiter=self.VALUE_SEPARATOR, quotechar=self.QUOTE_CHAR)

    try:
      row = reader.next()
    except (csv.Error, StopIteration):
      raise errors.UnableToParseFile(
          u'[{0:s}] Unable to parse CSV file: {1:s}.'.format(
              self.NAME, path_spec_printable))

    number_of_columns = len(self.COLUMNS)
    number_of_records = len(row)

    if number_of_records != number_of_columns:
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to parse CSV file: {1:s}. Wrong number of '
          u'records (expected: {2:d}, got: {3:d})').format(
              self.NAME, path_spec_printable, number_of_columns,
              number_of_records))

    for key, value in row.items():
      if key == self.MAGIC_TEST_STRING or value == self.MAGIC_TEST_STRING:
        raise errors.UnableToParseFile((
            u'[{0:s}] Unable to parse CSV file: {1:s}. Signature '
            u'mismatch.').format(self.NAME, path_spec_printable))

    if not self.VerifyRow(parser_mediator, row):
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to parse CSV file: {1:s}. Verification '
          u'failed.').format(self.NAME, path_spec_printable))

    row = self._ConvertRowToUnicode(parser_mediator, row)
    self.ParseRow(parser_mediator, text_file_object.tell(), row)

    for row in reader:
      if parser_mediator.abort:
        break
      row = self._ConvertRowToUnicode(parser_mediator, row)
      self.ParseRow(parser_mediator, text_file_object.tell(), row)

  def VerifyRow(self, unused_parser_mediator, unused_row):
    """Return a bool indicating whether or not this is the correct parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, bytes]): a single row from the CSV file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    pass


# TODO: determine if this method should be merged with PyParseIntCast.
def ConvertTokenToInteger(unused_string, unused_location, tokens):
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
  def CheckRange(unused_string, unused_location, tokens):
    """Parse the arguments.

    Args:
      location (int): location within the string where the match was made.
      tokens (list[str]): tokens.
    """
    try:
      check_number = tokens[0]
    except IndexError:
      check_number = -1

    if check_number < lower_bound:
      raise pyparsing.ParseException(
          u'Value: {0:d} precedes lower bound: {1:d}'.format(
              check_number, lower_bound))

    if check_number > upper_bound:
      raise pyparsing.ParseException(
          u'Value: {0:d} exceeds upper bound: {1:d}'.format(
              check_number, upper_bound))

  # Since callback methods for pyparsing need to accept certain parameters
  # and there is no way to define conditions, like upper and lower bounds
  # we need to return here a method that accepts those pyparsing parameters.
  return CheckRange


def PyParseIntCast(unused_string, unused_location, tokens):
  """Return an integer from a string.

  This is a pyparsing callback method that converts the matched
  string into an integer.

  The method modifies the content of the tokens list and converts
  them all to an integer value.

  Args:
    string (str): original parsed string.
    location (int): location within the string where the match was made.
    tokens (list[str]): extracted tokens, where the string to be converted
        is stored.
  """
  # Cast the regular tokens.
  for index, token in enumerate(tokens):
    try:
      tokens[index] = int(token)
    except ValueError:
      logging.error(u'Unable to cast [{0:s}] to an int, setting to 0'.format(
          token))
      tokens[index] = 0

  # We also need to cast the dictionary built tokens.
  for key in tokens.keys():
    try:
      tokens[key] = int(tokens[key], 10)
    except ValueError:
      logging.error(
          u'Unable to cast [{0:s} = {1:d}] to an int, setting to 0'.format(
              key, tokens[key]))
      tokens[key] = 0


def PyParseJoinList(unused_string, unused_location, tokens):
  """Return a joined token from a list of tokens.

  This is a callback method for pyparsing setParseAction that modifies
  the returned token list to join all the elements in the list to a single
  token.

  Args:
    string (str): original parsed string.
    location (int): location within the string where the match was made.
    tokens (list[str]): extracted tokens, where the string to be converted
        is stored.
  """
  join_list = []
  for token in tokens:
    try:
      join_list.append(str(token))
    except UnicodeDecodeError:
      join_list.append(repr(token))

  tokens[0] = u''.join(join_list)
  del tokens[1:]


class PyparsingConstants(object):
  """A class that maintains constants for pyparsing."""

  # Numbers.
  INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(PyParseIntCast)
  IPV4_OCTET = pyparsing.Word(pyparsing.nums, min=1, max=3).setParseAction(
      PyParseIntCast, PyParseRangeCheck(0, 255))
  IPV4_ADDRESS = (IPV4_OCTET + ('.' + IPV4_OCTET) * 3).setParseAction(
      PyParseJoinList)

  # TODO: Fix the IPv6 address specification to be more accurate (8 :, correct
  # size, etc).
  IPV6_ADDRESS = pyparsing.Word(':' + pyparsing.hexnums).setParseAction(
      PyParseJoinList)

  IP_ADDRESS = (IPV4_ADDRESS | IPV6_ADDRESS)

  # TODO: deprecate and remove, use THREE_LETTERS instead.
  MONTH = pyparsing.Word(
      pyparsing.string.uppercase, pyparsing.string.lowercase, exact=3)

  # Define date structures.
  HYPHEN = pyparsing.Literal(u'-').suppress()

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
      FOUR_DIGITS.setResultsName(u'year') + pyparsing.Suppress(u'-') +
      TWO_DIGITS.setResultsName(u'month') + pyparsing.Suppress(u'-') +
      TWO_DIGITS.setResultsName(u'day_of_month'))
  TIME_ELEMENTS = (
      TWO_DIGITS.setResultsName(u'hours') + pyparsing.Suppress(':') +
      TWO_DIGITS.setResultsName(u'minutes') + pyparsing.Suppress(':') +
      TWO_DIGITS.setResultsName(u'seconds'))
  TIME_MSEC_ELEMENTS = (
      TIME_ELEMENTS + pyparsing.Suppress('.') +
      INTEGER.setResultsName(u'microseconds'))

  # Date structures defined as a single group.
  DATE = pyparsing.Group(DATE_ELEMENTS)
  DATE_TIME = pyparsing.Group(DATE_ELEMENTS + TIME_ELEMENTS)
  DATE_TIME_MSEC = pyparsing.Group(DATE_ELEMENTS + TIME_MSEC_ELEMENTS)
  TIME = pyparsing.Group(TIME_ELEMENTS)

  TIME_MSEC = TIME + pyparsing.Suppress('.') + INTEGER
  # TODO: replace by
  # TIME_MSEC = pyparsing.Group(TIME_MSEC_ELEMENTS)

  COMMENT_LINE_HASH = pyparsing.Literal(u'#') + pyparsing.SkipTo(
      pyparsing.LineEnd())
  # TODO: Add more commonly used structs that can be used by parsers.
  PID = pyparsing.Word(
      pyparsing.nums, min=1, max=5).setParseAction(PyParseIntCast)


class PyparsingSingleLineTextParser(interface.FileObjectParser):
  """Single line text parser based on the pyparsing library."""

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

  # Define an encoding. If a file is encoded using specific encoding it is
  # advised to include it here. If this class constant is set all lines wil be
  # decoded prior to being sent to parsing by pyparsing, if not properly set it
  # could negatively affect parsing of the file.
  # If this value needs to be calculated on the fly (not a fixed constant for
  # this particular file type) it can be done by modifying the self.encoding
  # attribute.
  _ENCODING = u'ascii'

  _EMPTY_LINES = frozenset([b'\n', b'\r', b'\r\n'])

  def __init__(self):
    """Initializes a parser object."""
    super(PyparsingSingleLineTextParser, self).__init__()
    self._current_offset = 0
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures = self.LINE_STRUCTURES
    self.encoding = self._ENCODING

  def _ReadLine(
      self, parser_mediator, text_file_object, max_len=0, quiet=False, depth=0):
    """Reads a line from a text file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      text_file_object (dfvfs.TextFile): text file.
      max_len (Optional[int]): maximum number of bytes a single line can take.
      quiet (Optional[bool]): True if parse warnings should not be displayed.
      depth (Optional[int]): number of new lines the parser can encounter
          before bailing out.

    Returns:
      str: single line read from the file-like object, or the maximum number of
          characters, if max_len defined and line longer than the defined size.
    """
    if max_len:
      line = text_file_object.readline(max_len)
    else:
      line = text_file_object.readline()

    if not line:
      return

    if line in self._EMPTY_LINES:
      # Max 40 new lines in a row before we bail out.
      if depth == 40:
        return u''

      return self._ReadLine(
          parser_mediator, text_file_object, max_len=max_len, depth=depth + 1)

    if not self.encoding:
      return line.strip()

    try:
      line = line.decode(self.encoding)
    except UnicodeDecodeError:
      if not quiet:
        parser_mediator.ProduceExtractionError(
            u'unable to decode line: "{0:s}..." with encoding: {1:s}'.format(
                repr(line[:30]), self.encoding))

    return line.strip()

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
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
          u'Line structure undeclared, unable to proceed.')

    text_file_object = text_file.TextFile(file_object)

    line = self._ReadLine(
        parser_mediator, text_file_object, max_len=self.MAX_LINE_LENGTH,
        quiet=True)
    if not line:
      raise errors.UnableToParseFile(u'Not a text file.')

    if len(line) == self.MAX_LINE_LENGTH or len(
        line) == self.MAX_LINE_LENGTH - 1:
      logging.debug((
          u'Trying to read a line and reached the maximum allowed length of '
          u'{0:d}. The last few bytes of the line are: {1:s} [parser '
          u'{2:s}]').format(
              self.MAX_LINE_LENGTH, repr(line[-10:]), self.NAME))

    if not utils.IsText(line):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    if not self.VerifyStructure(parser_mediator, line):
      raise errors.UnableToParseFile(u'Wrong file structure.')

    # Set the offset to the beginning of the file.
    self._current_offset = 0
    # Read every line in the text file.
    while line:
      if parser_mediator.abort:
        break
      parsed_structure = None
      use_key = None
      # Try to parse the line using all the line structures.
      for key, structure in self.LINE_STRUCTURES:
        try:
          parsed_structure = structure.parseString(line)
        except pyparsing.ParseException:
          pass
        if parsed_structure:
          use_key = key
          break

      if parsed_structure:
        parsed_event = self.ParseRecord(
            parser_mediator, use_key, parsed_structure)
        if parsed_event:
          parsed_event.offset = self._current_offset
          parser_mediator.ProduceEvent(parsed_event)
      else:
        if len(line) > 80:
          line = u'{0:s}...'.format(line[:77])
        parser_mediator.ProduceExtractionError(
            u'unable to parse log line: {0:s} at offset {1:d}'.format(
                repr(line), self._current_offset))

      self._current_offset = text_file_object.get_offset()
      line = self._ReadLine(parser_mediator, text_file_object)

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
  """Class to read simple encoded text."""

  def __init__(self, buffer_size=2048, encoding=None):
    """Initializes the encoded test reader object.

    Args:
      buffer_size (Optional[int]): buffer size.
      encoding (Optional[str]): encoding.
    """
    super(EncodedTextReader, self).__init__()
    self._buffer = b''
    self._buffer_size = buffer_size
    self._current_offset = 0
    self._encoding = encoding

    if self._encoding:
      self._new_line = u'\n'.encode(self._encoding)
      self._carriage_return = u'\r'.encode(self._encoding)
    else:
      self._new_line = b'\n'
      self._carriage_return = b'\r'

    self._new_line_length = len(self._new_line)
    self._carriage_return_length = len(self._carriage_return)

    self.lines = u''

  def _ReadLine(self, file_object):
    """Reads a line from the file object.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      str: line read from the file-like object.
    """
    if len(self._buffer) < self._buffer_size:
      self._buffer = b''.join([
          self._buffer, file_object.read(self._buffer_size)])

    line, new_line, self._buffer = self._buffer.partition(self._new_line)
    if not line and not new_line:
      line = self._buffer
      self._buffer = b''

    self._current_offset += len(line)

    # Strip carriage returns from the text.
    if line.endswith(self._carriage_return):
      line = line[:-self._carriage_return_length]

    if new_line:
      line = b''.join([line, self._new_line])
      self._current_offset += self._new_line_length

    # If a parser specifically indicates specific encoding we need
    # to handle the buffer as it is an encoded string.
    # If it fails we fail back to the original raw string.
    if self._encoding:
      try:
        line = line.decode(self._encoding)
      except UnicodeDecodeError:
        # TODO: it might be better to raise here.
        pass

    return line

  def ReadLine(self, file_object):
    """Reads a line.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      str: line read from the lines buffer.
    """
    line, _, self.lines = self.lines.partition(u'\n')
    if not line:
      self.ReadLines(file_object)
      line, _, self.lines = self.lines.partition(u'\n')

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

        self.lines = u''.join([self.lines, line])
        lines_size -= len(line)

  def Reset(self):
    """Resets the encoded text reader."""
    self._buffer = b''
    self._current_offset = 0

    self.lines = u''

  def SkipAhead(self, file_object, number_of_characters):
    """Skips ahead a number of characters.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      number_of_characters (int): number of characters.
    """
    lines_size = len(self.lines)
    while number_of_characters >= lines_size:
      number_of_characters -= lines_size

      self.lines = u''
      self.ReadLines(file_object)
      lines_size = len(self.lines)
      if lines_size == 0:
        return

    self.lines = self.lines[number_of_characters:]


class PyparsingMultiLineTextParser(PyparsingSingleLineTextParser):
  """Multi line text parser based on the pyparsing library."""

  BUFFER_SIZE = 2048

  def __init__(self):
    """Initializes a parser object."""
    super(PyparsingMultiLineTextParser, self).__init__()
    self._buffer_size = self.BUFFER_SIZE
    self._text_reader = EncodedTextReader(
        buffer_size=self.BUFFER_SIZE, encoding=self._ENCODING)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a text file-like object using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not self.LINE_STRUCTURES:
      raise errors.UnableToParseFile(u'Missing line structures.')

    self._text_reader.Reset()

    try:
      self._text_reader.ReadLines(file_object)
    except UnicodeDecodeError as exception:
      raise errors.UnableToParseFile(
          u'Not a text file, with error: {0:s}'.format(exception))

    if not utils.IsText(self._text_reader.lines):
      raise errors.UnableToParseFile(u'Not a text file, unable to proceed.')

    if not self.VerifyStructure(parser_mediator, self._text_reader.lines):
      raise errors.UnableToParseFile(u'Wrong file structure.')

    # Using parseWithTabs() overrides Pyparsing's default replacement of tabs
    # with spaces to SkipAhead() the correct number of bytes after a match.
    for key, structure in self.LINE_STRUCTURES:
      structure.parseWithTabs()

    # Read every line in the text file.
    while self._text_reader.lines:
      if parser_mediator.abort:
        break

      # Initialize pyparsing objects.
      tokens = None
      start = 0
      end = 0

      key = None

      # Try to parse the line using all the line structures.
      for key, structure in self.LINE_STRUCTURES:
        try:
          structure_generator = structure.scanString(
              self._text_reader.lines, maxMatches=1)
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
        try:
          self.ParseRecord(parser_mediator, key, tokens)
        except (errors.ParseError, errors.TimestampError) as exception:
          parser_mediator.ProduceExtractionError(
              u'unable parse record: {0:s} with error: {1:s}'.format(
                  key, exception))

        self._text_reader.SkipAhead(file_object, end)

      else:
        odd_line = self._text_reader.ReadLine(file_object)
        if odd_line:
          if len(odd_line) > 80:
            odd_line = u'{0:s}...'.format(odd_line[:77])
          parser_mediator.ProduceExtractionError(
              u'unable to parse log line: {0:s}'.format(repr(odd_line)))

      try:
        self._text_reader.ReadLines(file_object)
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to read lines with error: {0:s}'.format(exception))

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
