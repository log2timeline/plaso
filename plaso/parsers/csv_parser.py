# -*- coding: utf-8 -*-
"""Comma seperated values (CSV) parser interface."""

from __future__ import unicode_literals

import abc
import csv
import os

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.parsers import interface


# The Python 2 version of the csv module does not support Unicode input
# and we cannot use dfvfs.TextFile. csv.DictReader requires a file-like
# object that implements readline. BinaryLineReader provides readline on top
# of dfvfs.FileIO objects.


class BinaryLineReader(object):
  """Line reader for binary file-like objects."""

  # The size of the lines buffer.
  _LINES_BUFFER_SIZE = 1024 * 1024

  # The maximum allowed size of the read buffer.
  _MAXIMUM_READ_BUFFER_SIZE = 16 * 1024 * 1024

  def __init__(self, file_object, end_of_line=b'\n'):
    """Initializes the line reader.

    Args:
      file_object (FileIO): a file-like object to read from.
      end_of_line (Optional[str]): end of line indicator.
    """
    super(BinaryLineReader, self).__init__()
    self._file_object = file_object
    self._file_object_size = file_object.get_size()
    self._end_of_line = end_of_line
    self._lines_buffer = b''
    self._lines_buffer_offset = 0
    self._lines_buffer_size = 0
    self._current_offset = 0

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def __iter__(self):
    """Returns a line of text.

    Yields:
      bytes: line of text.
    """
    line = self.readline()
    while line:
      yield line
      line = self.readline()

  def _ReadLinesData(self, maximum_size=None):
    """Reads the lines data.

    The number of reads are minimized by using a lines buffer.

    Args:
      maximum_size (Optional[int]): maximum number of bytes to read from
         the file-like object, where None represents all remaining data.

    Raises:
      ValueError: if the maximum size is smaller than zero or exceeds the
          maximum (as defined by _MAXIMUM_READ_BUFFER_SIZE).
    """
    if maximum_size is not None and maximum_size < 0:
      raise ValueError('Invalid maximum size value smaller than zero.')

    if (maximum_size is not None and
        maximum_size > self._MAXIMUM_READ_BUFFER_SIZE):
      raise ValueError('Invalid maximum size value exceeds maximum.')

    if self._lines_buffer_offset >= self._file_object_size:
      return b''

    if maximum_size is None:
      read_size = self._MAXIMUM_READ_BUFFER_SIZE
    else:
      read_size = maximum_size

    if self._lines_buffer_offset + read_size > self._file_object_size:
      read_size = self._file_object_size - self._lines_buffer_offset

    if read_size > self._lines_buffer_size:
      data = self._lines_buffer
      self._lines_buffer = b''

      # Read the remaining requested data and a full lines buffer at once.
      read_size -= self._lines_buffer_size
      remaining_size = read_size
      read_size += self._LINES_BUFFER_SIZE

      if self._lines_buffer_offset + read_size > self._file_object_size:
        read_size = self._file_object_size - self._lines_buffer_offset

      self._file_object.seek(self._lines_buffer_offset, os.SEEK_SET)
      read_buffer = self._file_object.read(read_size)

      read_count = len(read_buffer)

      if remaining_size > read_count:
        remaining_size = read_count

      data += read_buffer[:remaining_size]

      if remaining_size < read_count:
        self._lines_buffer = read_buffer[remaining_size:]
        self._lines_buffer_size = read_count - remaining_size

      self._lines_buffer_offset += read_count

    else:
      data = self._lines_buffer[:read_size]

      self._lines_buffer = self._lines_buffer[read_size:]
      self._lines_buffer_size -= read_size

    return data

  # Note: that the following functions do not follow the style guide
  # because they are part of the readline file-like object interface.

  def readline(self, size=None):
    """Reads a single line of text.

    The functions reads one entire line from the file-like object.
    A trailing end-of-line indicator (newline by default) is kept in the
    string (but may be absent when a file ends with an incomplete line).
    If the size argument is present and non-negative, it is a maximum byte
    count (including the trailing end-of-line) and an incomplete line may
    be returned. An empty string is returned only when end-of-file is
    encountered immediately.

    Args:
      size (Optional[int]): maximum string size to read.

    Returns:
      bytes: line of text.
    """
    if size is None or size <= 0:
      size = None

    next_offset = self._current_offset + self._lines_buffer_size

    if (self._end_of_line not in self._lines_buffer and
        next_offset == self._file_object_size):
      line = self._lines_buffer
      self._lines_buffer_size = 0
      self._lines_buffer = b''

      return line
    elif (self._end_of_line not in self._lines_buffer and
          (size is None or self._lines_buffer_size < size)):
      lines_data = self._ReadLinesData(size)

      result, separator, lines_data = lines_data.partition(self._end_of_line)

      if lines_data:
        self._lines_buffer = b''.join([lines_data, self._lines_buffer])
        self._lines_buffer_size = len(self._lines_buffer)

    else:
      result, separator, self._lines_buffer = self._lines_buffer.partition(
          self._end_of_line)
      self._lines_buffer_size -= len(result + separator)

    line = b''.join([result, separator])
    self._current_offset += len(line)

    return line

  def readlines(self, sizehint=None):
    """Reads lines of text.

    The function reads until EOF using readline() and return a list
    containing the lines read. If the optional sizehint argument is
    present, instead of reading up to EOF, whole lines totalling
    approximately sizehint bytes (possibly after rounding up to
    an internal buffer size) are read.

    Args:
      sizehint (Optional[int]): maximum byte size to read.

    Returns:
      list[bytes]: lines of text.
    """
    if sizehint is None or sizehint <= 0:
      sizehint = None

    lines = []
    lines_byte_size = 0
    line = self.readline()

    while line:
      lines.append(line)

      if sizehint is not None:
        lines_byte_size += len(line)

        if lines_byte_size >= sizehint:
          break

      line = self.readline()

    return lines

  # get_offset() is preferred above tell() by the libbfio layer used in libyal.
  def get_offset(self):
    """Retrieves the current offset into the file-like object.

    Returns:
      int: cuffent offset into the file-like object.
    """
    return self._current_offset

  # Pythonesque alias for get_offet().
  def tell(self):
    """Retrieves the current offset into the file-like object.

    Returns:
      int: cuffent offset into the file-like object.
    """
    return self._current_offset


class CSVParser(interface.FileObjectParser):
  """Comma seperated values (CSV) parser interface."""

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
  _MAGIC_TEST_STRING = b'RegnThvotturMeistarans'

  def __init__(self, encoding=None):
    """Initializes a CSV parser.

    Args:
      encoding (Optional[str]): encoding used in the CSV file, where None
          indicates the codepage of the parser mediator should be used.
    """
    super(CSVParser, self).__init__()
    self._encoding = encoding

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
    encoding = self._encoding or parser_mediator.codepage

    for key, value in iter(row.items()):
      if isinstance(value, py2to3.UNICODE_TYPE):
        continue

      try:
        row[key] = value.decode(encoding)
      except UnicodeDecodeError:
        replaced_value = value.decode(encoding, errors='replace')
        parser_mediator.ProduceExtractionError(
            'error decoding CSV value: {0:s} as {1:s}, characters have been '
            'replaced in {2:s}'.format(key, encoding, replaced_value))
        row[key] = replaced_value

    return row

  def ParseFileObject(self, parser_mediator, file_object, **unused_kwargs):
    """Parses a CSV text file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    line_reader = BinaryLineReader(file_object)

    # If we specifically define a number of lines we should skip, do that here.
    for _ in range(0, self.NUMBER_OF_HEADER_LINES):
      line_reader.readline()

    reader = csv.DictReader(
        line_reader, delimiter=self.VALUE_SEPARATOR,
        fieldnames=self.COLUMNS, quotechar=self.QUOTE_CHAR,
        restkey=self._MAGIC_TEST_STRING, restval=self._MAGIC_TEST_STRING)

    row_offset = line_reader.tell()
    try:
      row = next(reader)
    except (StopIteration, csv.Error):
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile(
          '[{0:s}] Unable to parse CSV file: {1:s}.'.format(
              self.NAME, display_name))

    number_of_columns = len(self.COLUMNS)
    number_of_records = len(row)

    if number_of_records != number_of_columns:
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile((
          '[{0:s}] Unable to parse CSV file: {1:s}. Wrong number of '
          'records (expected: {2:d}, got: {3:d})').format(
              self.NAME, display_name, number_of_columns,
              number_of_records))

    for key, value in row.items():
      if self._MAGIC_TEST_STRING in (key, value):
        display_name = parser_mediator.GetDisplayName()
        raise errors.UnableToParseFile((
            '[{0:s}] Unable to parse CSV file: {1:s}. Signature '
            'mismatch.').format(self.NAME, display_name))

    if not self.VerifyRow(parser_mediator, row):
      display_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile((
          '[{0:s}] Unable to parse CSV file: {1:s}. Verification '
          'failed.').format(self.NAME, display_name))

    row = self._ConvertRowToUnicode(parser_mediator, row)
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
    """Parses a line of the log file and extract events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the row.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.
    """

  @abc.abstractmethod
  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file corresponds with the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
