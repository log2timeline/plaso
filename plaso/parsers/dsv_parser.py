# -*- coding: utf-8 -*-
"""Delimiter separated values (DSV) parser interface."""

from __future__ import unicode_literals

import abc
import csv

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.lib import line_reader_file
from plaso.lib import py2to3
from plaso.lib import specification
from plaso.parsers import interface


# The Python 2 version of the csv module does not support Unicode input
# and we cannot use dfvfs.TextFile. csv.DictReader requires a file-like
# object that implements readline. BinaryLineReader provides readline on top
# of dfvfs.FileIO objects.


class DSVParser(interface.FileObjectParser):
  """Delimiter separated values (DSV) parser interface."""

  # A list that contains the names of all the fields in the log file. This
  # needs to be defined by each DSV parser.
  COLUMNS = []

  # The default delimiter is a comma, but a tab, pipe or other character are
  # known to be used. Note the delimiter must be a byte string otherwise csv
  # module can raise a TypeError indicating that "delimiter" must be a single
  # character string.
  DELIMITER = b','

  # If there is a header before the lines start it can be defined here, and
  # the number of header lines that need to be skipped before the parsing
  # starts.
  NUMBER_OF_HEADER_LINES = 0

  # If there is a special quote character used inside the structured text
  # it can be defined here.
  QUOTE_CHAR = b'"'

  # Value that should not appear inside the file, made to test the actual
  # file to see if it confirms to standards.
  _MAGIC_TEST_STRING = b'RegnThvotturMeistarans'

  # Maximum supported file size of 16 MiB.
  _MAXIMUM_SUPPORTED_FILE_SIZE = 16 * 1024 * 1024

  def __init__(self, encoding=None):
    """Initializes a delimiter separated values (DSV) parser.

    Args:
      encoding (Optional[str]): encoding used in the DSV file, where None
          indicates the codepage of the parser mediator should be used.
    """
    super(DSVParser, self).__init__()
    self._encoding = encoding

  def _ConvertRowToUnicode(self, parser_mediator, row):
    """Converts all strings in a DSV row dict to Unicode.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, bytes]): a row from a DSV file, where the dictionary
          key contains the column name and the value a binary string.

    Returns:
      dict[str, str]: a row from the DSV file, where the dictionary key
          contains the column name and the value a Unicode string.
    """
    for key, value in iter(row.items()):
      if isinstance(value, py2to3.UNICODE_TYPE):
        continue

      try:
        row[key] = value.decode(self._encoding)
      except UnicodeDecodeError:
        replaced_value = value.decode(self._encoding, errors='replace')
        parser_mediator.ProduceExtractionError(
            'error decoding DSV value: {0:s} as {1:s}, characters have been '
            'replaced in {2:s}'.format(key, self._encoding, replaced_value))
        row[key] = replaced_value

    return row

  def _CreateDictReader(self, line_reader):
    """Returns a reader that processes each row and yields dictionaries.

    csv.DictReader does this job well for single-character delimiters; parsers
    that need multi-character delimiters need to override this method.

    Args:
      line_reader (iter): yields lines from a file-like object.

    Returns:
      iter: a reader of dictionaries, as returned by csv.DictReader().
    """
    delimiter = self.DELIMITER
    quotechar = self.QUOTE_CHAR
    magic_test_string = self._MAGIC_TEST_STRING
    # Python 3 csv module requires arguments to constructor to be of type str.
    if py2to3.PY_3:
      delimiter = delimiter.decode(self._encoding)
      quotechar = quotechar.decode(self._encoding)
      magic_test_string = magic_test_string.decode(self._encoding)

    return csv.DictReader(
        line_reader, delimiter=delimiter, fieldnames=self.COLUMNS,
        quotechar=quotechar, restkey=magic_test_string,
        restval=magic_test_string)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    return specification.FormatSpecification(cls.NAME, text_format=True)

  def ParseFileObject(self, parser_mediator, file_object, **unused_kwargs):
    """Parses a DSV text file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_size = file_object.get_size()
    # The csv module can consume a lot of memory, 1 GiB for a 100 MiB file.
    # Hence that the maximum supported file size is restricted.
    if file_size > self._MAXIMUM_SUPPORTED_FILE_SIZE:
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile((
          '[{0:s}] Unable to parse DSV file: {1:s} size of file exceeds '
          'maximum supported size').format(self.NAME, display_name))

    # TODO: Replace this with detection of the file encoding via byte-order
    # marks. Also see: https://github.com/log2timeline/plaso/issues/1971
    if not self._encoding:
      self._encoding = parser_mediator.codepage

    # The Python 2 csv module reads bytes and the Python 3 csv module Unicode
    # reads strings.
    if py2to3.PY_3:
      line_reader = text_file.TextFile(file_object, encoding=self._encoding)
    else:
      line_reader = line_reader_file.BinaryLineReader(file_object)

    # If we specifically define a number of lines we should skip, do that here.
    for _ in range(0, self.NUMBER_OF_HEADER_LINES):
      line_reader.readline()

    reader = self._CreateDictReader(line_reader)

    row_offset = line_reader.tell()
    try:
      row = next(reader)
    except (StopIteration, csv.Error) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile(
          '[{0:s}] Unable to parse DSV file: {1:s} with error: {2!s}.'.format(
              self.NAME, display_name, exception))

    number_of_columns = len(self.COLUMNS)
    number_of_records = len(row)

    if number_of_records != number_of_columns:
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile((
          '[{0:s}] Unable to parse DSV file: {1:s}. Wrong number of '
          'records (expected: {2:d}, got: {3:d})').format(
              self.NAME, display_name, number_of_columns,
              number_of_records))

    for key, value in row.items():
      if self._MAGIC_TEST_STRING in (key, value):
        display_name = parser_mediator.GetDisplayName()
        raise errors.UnableToParseFile((
            '[{0:s}] Unable to parse DSV file: {1:s}. Signature '
            'mismatch.').format(self.NAME, display_name))

    row = self._ConvertRowToUnicode(parser_mediator, row)

    if not self.VerifyRow(parser_mediator, row):
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile((
          '[{0:s}] Unable to parse DSV file: {1:s}. Verification '
          'failed.').format(self.NAME, display_name))

    self.ParseRow(parser_mediator, row_offset, row)
    row_offset = line_reader.tell()

    for row in reader:
      if parser_mediator.abort:
        break
      row = self._ConvertRowToUnicode(parser_mediator, row)
      self.ParseRow(parser_mediator, row_offset, row)
      row_offset = line_reader.tell()

  @abc.abstractmethod
  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """

  @abc.abstractmethod
  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
