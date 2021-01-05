#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the delimiter separated values (DSV) parser."""

import io
import unittest

from plaso.parsers import dsv_parser

from tests.parsers import test_lib


class TestDSVParser(dsv_parser.DSVParser):
  """Delimiter separated values (DSV) parser parser for testing.

  Attribute:
    row_offsets[list[int]: offsets of the rows extracted by the DSV parser.
    row[list[dict[str, str]]]: rows extracted by the DSV parser.
  """

  COLUMNS = ['place', 'user', 'password']
  NUMBER_OF_HEADER_LINES = 1

  _ENCODING = 'utf-8'

  def __init__(self):
    """Initializes a DSV parser."""
    super(TestDSVParser, self).__init__()
    self.row_offsets = []
    self.rows = []

  # pylint: disable=unused-argument
  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and extract events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      row_offset (int): offset of the row.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.
    """
    self.row_offsets.append(row_offset)
    self.rows.append(row)

  # pylint: disable=unused-argument
  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file corresponds with the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return True


class DSVParserTest(test_lib.ParserTestCase):
  """Tests the delimiter separated values (DSV) parser."""

  # pylint: disable=protected-access

  def testCheckForByteOrderMark(self):
    """Tests the _CheckForByteOrderMark function."""
    parser = TestDSVParser()

    file_object = io.BytesIO(b'\xef\xbb\xbfUTF-8')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertEqual(encoding, 'utf-8')
    self.assertEqual(text_offset, 3)

    file_object = io.BytesIO(b'\xfe\xffUTF-16 big-endian')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertEqual(encoding, 'utf-16-be')
    self.assertEqual(text_offset, 2)

    file_object = io.BytesIO(b'\xff\xfeUTF-16 little-endian')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertEqual(encoding, 'utf-16-le')
    self.assertEqual(text_offset, 2)

    file_object = io.BytesIO(b'\x00\x00\xfe\xffUTF-32 big-endian')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertEqual(encoding, 'utf-32-be')
    self.assertEqual(text_offset, 4)

    file_object = io.BytesIO(b'\xff\xfe\x00\x00UTF-32 little-endian')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertEqual(encoding, 'utf-32-le')
    self.assertEqual(text_offset, 4)

    file_object = io.BytesIO(b'ASCII')
    encoding, text_offset = parser._CheckForByteOrderMark(file_object)

    self.assertIsNone(encoding)
    self.assertEqual(text_offset, 0)

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = TestDSVParser()

    self._ParseFile(['password.csv'], parser)

    self.assertEqual(len(parser.rows), 4)

    row_offset = parser.row_offsets[0]
    self.assertEqual(row_offset, 20)

    row = parser.rows[0]
    self.assertEqual(row['place'], 'bank')
    self.assertEqual(row['user'], 'joesmith')
    self.assertEqual(row['password'], 'superrich')

  def testHasExpectedLineLength(self):
    """Tests the _HasExpectedLineLength function."""
    parser = TestDSVParser()
    test_file_entry = self._GetTestFileEntry(['password.csv'])
    test_file_object = test_file_entry.GetFileObject()

    self.assertTrue(parser._HasExpectedLineLength(
        test_file_object, encoding='utf-8'))

    parser._maximum_line_length = 2
    parser._HasExpectedLineLength(
        test_file_object, encoding='utf-8')
    self.assertFalse(parser._HasExpectedLineLength(
        test_file_object, encoding='utf-8'))


if __name__ == '__main__':
  unittest.main()
