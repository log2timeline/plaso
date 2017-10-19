#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the comma seperated values (CSV) parser."""

from __future__ import unicode_literals

import unittest

from dfvfs.file_io import os_file_io
from dfvfs.path import os_path_spec
from dfvfs.resolver import context

from plaso.parsers import csv_parser

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class TestCSVParser(csv_parser.CSVParser):
  """CSV parser for testing.

  Attribute:
    row_offsets[list[int]: offsets of the rows extracted by the CSV parser.
    row[list[dict[str, str]]]: rows extracted by the CSV parser.
  """

  COLUMNS = ['place', 'user', 'password']
  NUMBER_OF_HEADER_LINES = 1

  def __init__(self):
    """Initializes a CSV parser."""
    super(TestCSVParser, self).__init__()
    self.row_offsets = []
    self.rows = []

  def ParseRow(self, unused_parser_mediator, row_offset, row):
    """Parses a line of the log file and extract events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the row.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.
    """
    self.row_offsets.append(row_offset)
    self.rows.append(row)

  def VerifyRow(self, unused_parser_mediator, unused_row):
    """Verifies if a line of the file corresponds with the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return True


@shared_test_lib.skipUnlessHasTestFile(['another_file'])
@shared_test_lib.skipUnlessHasTestFile(['password.txt'])
class BinaryLineReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the binary line reader."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._resolver_context = context.Context()
    test_file = self._GetTestFilePath(['another_file'])
    self._os_path_spec1 = os_path_spec.OSPathSpec(location=test_file)

    test_file = self._GetTestFilePath(['password.txt'])
    self._os_path_spec2 = os_path_spec.OSPathSpec(location=test_file)

  def testReadline(self):
    """Test the readline() function."""
    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(self._os_path_spec1)
    line_reader = csv_parser.BinaryLineReader(file_object)

    self.assertEqual(line_reader.readline(), b'This is another file.\n')

    self.assertEqual(line_reader.get_offset(), 22)

    file_object.close()

  def testReadlines(self):
    """Test the readlines() function."""
    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(self._os_path_spec2)
    line_reader = csv_parser.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 5)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')
    self.assertEqual(lines[3], b'treasure chest,-,1111\n')
    self.assertEqual(lines[4], b'uber secret laire,admin,admin\n')

    file_object.close()

  def testReadlinesWithSizeHint(self):
    """Test the readlines() function."""
    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(self._os_path_spec2)
    line_reader = csv_parser.BinaryLineReader(file_object)

    lines = line_reader.readlines(sizehint=60)

    self.assertEqual(len(lines), 3)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')

    file_object.close()

  @shared_test_lib.skipUnlessHasTestFile(['mactime.body'])
  def testReadlinesWithFileWithoutNewLineAtEnd(self):
    """Test reading lines from a file without a new line char at the end."""
    test_file = self._GetTestFilePath(['mactime.body'])
    test_file_path_spec = os_path_spec.OSPathSpec(location=test_file)
    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_file_path_spec)
    line_reader = csv_parser.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 17)

  def testIterator(self):
    """Test the iterator functionality."""
    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(self._os_path_spec2)
    line_reader = csv_parser.BinaryLineReader(file_object)

    lines = []
    for line in line_reader:
      lines.append(line)

    self.assertEqual(len(lines), 5)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')
    self.assertEqual(lines[3], b'treasure chest,-,1111\n')
    self.assertEqual(lines[4], b'uber secret laire,admin,admin\n')

    file_object.close()

  # TODO: Add a test which tests reading a file which is
  # larger than the buffer size, and read lines until it crosses
  # that original buffer size (to test if the buffer is correctly
  # filled).


class CSVParserTest(test_lib.ParserTestCase):
  """Tests the comma seperated values (CSV) parser."""

  # pylint: disable=protected-access

  def testConvertRowToUnicode(self):
    """Tests the _ConvertRowToUnicode function."""
    binary_row = {
        'place': b'bank',
        'user': b'joesmith',
        'password': b'superr\xc3\xadch'}

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = csv_parser.CSVParser(encoding='utf-8')

    unicode_row = parser._ConvertRowToUnicode(parser_mediator, binary_row)
    self.assertEqual(unicode_row['password'], 'superrích')

    # Convert Unicode values.
    unicode_row = parser._ConvertRowToUnicode(parser_mediator, unicode_row)
    self.assertEqual(unicode_row['password'], 'superrích')

    knowledge_base_values = {'codepage': 'ascii'}
    parser_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base_values=knowledge_base_values)
    self.assertEqual(parser_mediator.codepage, 'ascii')

    parser = csv_parser.CSVParser()

    unicode_row = parser._ConvertRowToUnicode(parser_mediator, binary_row)
    self.assertEqual(unicode_row['password'], 'superr\xedch')

  @shared_test_lib.skipUnlessHasTestFile(['password.txt'])
  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = TestCSVParser()

    self._ParseFile(['password.txt'], parser)

    self.assertEqual(len(parser.rows), 4)

    row_offset = parser.row_offsets[0]
    self.assertEqual(row_offset, 20)

    row = parser.rows[0]
    self.assertEqual(row['place'], 'bank')
    self.assertEqual(row['user'], 'joesmith')
    self.assertEqual(row['password'], 'superrich')


if __name__ == '__main__':
  unittest.main()
