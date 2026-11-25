#!/usr/bin/env python3
"""Tests for the delimiter separated values (DSV) parser."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import dsv_parser

from tests.parsers import test_lib


class TestDSVParser(dsv_parser.DSVParser):
    """Delimiter separated values (DSV) parser parser for testing.

    Attribute:
      row_offsets[list[int]: offsets of the rows extracted by the DSV parser.
      row[list[dict[str, str]]]: rows extracted by the DSV parser.
    """

    COLUMNS = ["place", "user", "password"]
    NUMBER_OF_HEADER_LINES = 1

    _ENCODING = "utf-8"

    def __init__(self):
        """Initializes a DSV parser."""
        super().__init__()
        self.row_offsets = []
        self.rows = []

    # pylint: disable=unused-argument
    def ParseRow(self, parser_mediator, row_offset, row):
        """Parses a line of the log file and extract events.

        Args:
          parser_mediator (ParserMediator): mediates interactions between
              parsers and other components, such as storage and dfVFS.
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
              parsers and other components, such as storage and dfVFS.
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

        file_object = io.BytesIO(b"\xef\xbb\xbfUTF-8")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertEqual(encoding, "utf-8")
        self.assertEqual(text_offset, 3)

        file_object = io.BytesIO(b"\xfe\xffUTF-16 big-endian")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertEqual(encoding, "utf-16-be")
        self.assertEqual(text_offset, 2)

        file_object = io.BytesIO(b"\xff\xfeUTF-16 little-endian")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertEqual(encoding, "utf-16-le")
        self.assertEqual(text_offset, 2)

        file_object = io.BytesIO(b"\x00\x00\xfe\xffUTF-32 big-endian")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertEqual(encoding, "utf-32-be")
        self.assertEqual(text_offset, 4)

        file_object = io.BytesIO(b"\xff\xfe\x00\x00UTF-32 little-endian")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertEqual(encoding, "utf-32-le")
        self.assertEqual(text_offset, 4)

        file_object = io.BytesIO(b"ASCII")
        encoding, text_offset = parser._CheckForByteOrderMark(file_object)

        self.assertIsNone(encoding)
        self.assertEqual(text_offset, 0)

    def testParseFileObject(self):
        """Tests the ParseFileObject function."""
        parser = TestDSVParser()

        self._ParseFile(["password.csv"], parser)

        self.assertEqual(len(parser.rows), 4)

        row_offset = parser.row_offsets[0]
        self.assertEqual(row_offset, 20)

        row = parser.rows[0]
        self.assertEqual(row["place"], "bank")
        self.assertEqual(row["user"], "joesmith")
        self.assertEqual(row["password"], "superrich")

    def testCheckFirstRowInSampleData(self):
        """Tests the _CheckFirstRowInSampleData function."""
        parser = TestDSVParser()
        storage_writer = self._CreateStorageWriter()
        test_file_entry = self._GetTestFileEntry(["password.csv"])
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=test_file_entry
        )

        test_file_object = self._CreateFileObject(
            "first_row.csv", b"place,user,password\nbank,joesmith,superrich\n"
        )
        parser._CheckFirstRowInSampleData(parser_mediator, test_file_object, "utf-8")

        # Near-miss first rows that must not match.
        for data in (
            b"place,user,password\nbank,joesmith\n",
            b"place,user,password\nbank,joesmith,superrich,extra\n",
            b"place,user,password\nbank,\xff,superrich\n",
            b"place,user,password\nbank\r,joesmith,superrich\n",
        ):
            test_file_object = self._CreateFileObject("first_row.csv", data)
            with self.assertRaises(errors.WrongParser):
                parser._CheckFirstRowInSampleData(
                    parser_mediator, test_file_object, "utf-8"
                )

        # The first row is not complete in the sample data and is left to the line
        # reader.
        for data in (
            b"place,user,password",
            b"place,user,password\n",
            b"place,user,password\nbank,joesmith",
            b'place,user,password\n"bank\n',
        ):
            test_file_object = self._CreateFileObject("first_row.csv", data)
            parser._CheckFirstRowInSampleData(
                parser_mediator, test_file_object, "utf-8"
            )

    def testParseFileObjectWithFirstRowBeyondSampleData(self):
        """Tests the ParseFileObject function with a long first row."""
        parser = TestDSVParser()
        storage_writer = self._CreateStorageWriter()
        test_file_entry = self._GetTestFileEntry(["password.csv"])
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=test_file_entry
        )

        long_value = b"a" * parser._SAMPLE_DATA_SIZE
        test_file_object = self._CreateFileObject(
            "long_row.csv",
            b"".join([b"place,user,password\nbank,joesmith,", long_value, b"\n"]),
        )
        parser.ParseFileObject(parser_mediator, test_file_object)

        self.assertEqual(len(parser.rows), 1)
        self.assertEqual(parser.row_offsets, [20])
        self.assertEqual(len(parser.rows[0]["password"]), parser._SAMPLE_DATA_SIZE)

    def testReadCompleteLinesInSampleData(self):
        """Tests the _ReadCompleteLinesInSampleData function."""
        parser = TestDSVParser()

        sample_line_reader = parser._ReadCompleteLinesInSampleData(
            b"\xef\xbb\xbfplace,user\nbank,joesmith\nincomplete", "utf-8"
        )
        self.assertEqual(next(sample_line_reader), "place,user\n")
        self.assertEqual(next(sample_line_reader), "bank,joesmith\n")
        with self.assertRaises(dsv_parser._InsufficientSampleDataError):
            next(sample_line_reader)

        sample_line_reader = parser._ReadCompleteLinesInSampleData(
            b"place,user\n\xff\n", "utf-8"
        )
        self.assertEqual(next(sample_line_reader), "place,user\n")
        with self.assertRaises(UnicodeDecodeError):
            next(sample_line_reader)

    def testHasExpectedLineLength(self):
        """Tests the _HasExpectedLineLength function."""
        parser = TestDSVParser()
        test_file_entry = self._GetTestFileEntry(["password.csv"])
        test_file_object = test_file_entry.GetFileObject()

        self.assertTrue(
            parser._HasExpectedLineLength(test_file_object, encoding="utf-8")
        )

        parser._maximum_line_length = 2
        parser._HasExpectedLineLength(test_file_object, encoding="utf-8")
        self.assertFalse(
            parser._HasExpectedLineLength(test_file_object, encoding="utf-8")
        )

        # Only the first 20 lines after the header lines are checked.
        parser = TestDSVParser()
        long_line = b"a" * (parser._maximum_line_length + 1)
        short_lines = b"place,user,password\n" * 21

        test_file_object = self._CreateFileObject(
            "long_line.csv", b"".join([short_lines, long_line])
        )
        self.assertTrue(
            parser._HasExpectedLineLength(test_file_object, encoding="utf-8")
        )

        test_file_object = self._CreateFileObject(
            "long_line.csv", b"".join([short_lines[:200], long_line])
        )
        self.assertFalse(
            parser._HasExpectedLineLength(test_file_object, encoding="utf-8")
        )

        test_file_object = self._CreateFileObject(
            "long_line.csv", b"".join([short_lines[:200], b"\xff\n", long_line])
        )
        with self.assertRaises(UnicodeDecodeError):
            parser._HasExpectedLineLength(test_file_object, encoding="utf-8")

    def testHasExpectedLineLengthInSampleData(self):
        """Tests the _HasExpectedLineLengthInSampleData function."""
        parser = TestDSVParser()
        short_lines = b"place,user,password\n" * 21

        test_file_object = self._CreateFileObject("short_lines.csv", short_lines)
        result = parser._HasExpectedLineLengthInSampleData(test_file_object, "utf-8")
        self.assertTrue(result)

        # Lines after the first 20 lines after the header lines are not read.
        test_file_object = self._CreateFileObject(
            "short_lines.csv", b"".join([short_lines, b"\xff\n"])
        )
        result = parser._HasExpectedLineLengthInSampleData(test_file_object, "utf-8")
        self.assertTrue(result)

        test_file_object = self._CreateFileObject(
            "short_lines.csv", b"".join([b"\xff\n", short_lines])
        )
        with self.assertRaises(UnicodeDecodeError):
            parser._HasExpectedLineLengthInSampleData(test_file_object, "utf-8")

        # The sample data contains less than 20 lines after the header lines.
        test_file_object = self._CreateFileObject("short_lines.csv", short_lines[:200])
        result = parser._HasExpectedLineLengthInSampleData(test_file_object, "utf-8")
        self.assertIsNone(result)

        long_line = b"a" * parser._SAMPLE_DATA_SIZE
        test_file_object = self._CreateFileObject(
            "long_line.csv", b"".join([long_line, short_lines])
        )
        result = parser._HasExpectedLineLengthInSampleData(test_file_object, "utf-8")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
