#!/usr/bin/env python3
"""Tests for the binary line reader file-like object."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec
from dfvfs.path import os_path_spec
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import line_reader_file

from tests import test_lib as shared_test_lib


class SmallReadBufferBinaryLineReader(line_reader_file.BinaryLineReader):
    """Binary line reader with a small read buffer for testing."""

    MAXIMUM_READ_BUFFER_SIZE = 8


class BinaryLineReaderTest(shared_test_lib.BaseTestCase):
    """Tests for the binary line reader."""

    def setUp(self):
        """Sets up the needed objects used throughout the test."""
        self._resolver_context = context.Context()

    def _CreateLineReader(self, data, end_of_line=b"\n", small_read_buffer=False):
        """Creates a binary line reader for test data.

        Args:
          data (bytes): data of the test file.
          end_of_line (Optional[bytes]): end of line indicator.
          small_read_buffer (Optional[bool]): True if the line reader should use
              a read buffer of 8 bytes.

        Returns:
          BinaryLineReader: binary line reader.
        """
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile("/test.txt", data)

        test_path_spec = fake_path_spec.FakePathSpec(location="/test.txt")
        file_object = file_system_builder.file_system.GetFileObjectByPathSpec(
            test_path_spec
        )

        if small_read_buffer:
            line_reader_class = SmallReadBufferBinaryLineReader
        else:
            line_reader_class = line_reader_file.BinaryLineReader

        return line_reader_class(file_object, end_of_line=end_of_line)

    def testReadline(self):
        """Test the readline() function."""
        test_file_path = self._GetTestFilePath(["another_file"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        line = line_reader.readline()
        self.assertEqual(line, b"This is another file.\n")

        offset = line_reader.tell()
        self.assertEqual(offset, 22)

        line_reader = line_reader_file.BinaryLineReader(file_object)

        line = line_reader.readline(size=11)
        self.assertEqual(line, b"This is ano")

        offset = line_reader.tell()
        self.assertEqual(offset, 11)

    def testReadlineMultipleLines(self):
        """Test the readline() function on multiple lines."""
        test_file_path = self._GetTestFilePath(["password.csv"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        line = line_reader.readline()
        self.assertEqual(line, b"place,user,password\n")

        offset = line_reader.tell()
        self.assertEqual(offset, 20)

        line = line_reader.readline(size=5)
        self.assertEqual(line, b"bank,")

        offset = line_reader.tell()
        self.assertEqual(offset, 25)

        line = line_reader.readline()
        self.assertEqual(line, b"joesmith,superrich\n")

        offset = line_reader.tell()
        self.assertEqual(offset, 44)

        line = line_reader.readline()
        self.assertEqual(line, b"alarm system,-,1234\n")

        offset = line_reader.tell()
        self.assertEqual(offset, 64)

    def testReadlines(self):
        """Test the readlines() function."""
        test_file_path = self._GetTestFilePath(["password.csv"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        lines = line_reader.readlines()

        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], b"place,user,password\n")
        self.assertEqual(lines[1], b"bank,joesmith,superrich\n")
        self.assertEqual(lines[2], b"alarm system,-,1234\n")
        self.assertEqual(lines[3], b"treasure chest,-,1111\n")
        self.assertEqual(lines[4], b"uber secret laire,admin,admin\n")

    def testReadlinesWithSizeHint(self):
        """Test the readlines() function."""
        test_file_path = self._GetTestFilePath(["password.csv"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        lines = line_reader.readlines(sizehint=60)

        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], b"place,user,password\n")
        self.assertEqual(lines[1], b"bank,joesmith,superrich\n")
        self.assertEqual(lines[2], b"alarm system,-,1234\n")

    def testReadlinesWithFileWithoutNewLineAtEnd(self):
        """Test reading lines from a file without a new line char at the end."""
        test_file_path = self._GetTestFilePath(["bodyfile", "bodyfile"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        lines = line_reader.readlines()

        self.assertEqual(len(lines), 25)

    def testIterator(self):
        """Test the iterator functionality."""
        test_file_path = self._GetTestFilePath(["password.csv"])
        self._SkipIfPathNotExists(test_file_path)

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=self._resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        lines = []
        for line in line_reader:
            lines.append(line)

        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], b"place,user,password\n")
        self.assertEqual(lines[1], b"bank,joesmith,superrich\n")
        self.assertEqual(lines[2], b"alarm system,-,1234\n")
        self.assertEqual(lines[3], b"treasure chest,-,1111\n")
        self.assertEqual(lines[4], b"uber secret laire,admin,admin\n")

    def testReadlinesWithSingleLine(self):
        """Test the readlines() function on a file with a single line."""
        line_reader = self._CreateLineReader(b"x\n")

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"x\n"])
        self.assertEqual(line_reader.tell(), 2)

        line_reader = self._CreateLineReader(b"xy\r\n", end_of_line=b"\r\n")

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"xy\r\n"])
        self.assertEqual(line_reader.tell(), 4)

    def testReadlinesWithLinesCrossingReadBuffer(self):
        """Test the readlines() function with lines that cross the read buffer."""
        line_reader = self._CreateLineReader(b"aaaa\nbbbbbbb\n", small_read_buffer=True)

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"aaaa\n", b"bbbbbbb\n"])
        self.assertEqual(line_reader.tell(), 13)

        line_reader = self._CreateLineReader(
            b"aa\r\nbbbbbbbbb\r\n", end_of_line=b"\r\n", small_read_buffer=True
        )

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"aa\r\n", b"bbbbbbbbb\r\n"])
        self.assertEqual(line_reader.tell(), 15)

        test_data = b"abcdef\n" * 20
        line_reader = self._CreateLineReader(test_data, small_read_buffer=True)

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"abcdef\n"] * 20)
        self.assertEqual(line_reader.tell(), 140)

    def testReadlinesWithoutEndOfLineCrossingReadBuffer(self):
        """Test the readlines() function without end-of-line at the end."""
        line_reader = self._CreateLineReader(b"abcdef\nghij", small_read_buffer=True)

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"abcdef\n", b"ghij"])
        self.assertEqual(line_reader.tell(), 11)

        line_reader = self._CreateLineReader(
            b"abcde\r\nghij", end_of_line=b"\r\n", small_read_buffer=True
        )

        lines = line_reader.readlines()
        self.assertEqual(lines, [b"abcde\r\n", b"ghij"])
        self.assertEqual(line_reader.tell(), 11)


class BinaryDSVReaderTest(shared_test_lib.BaseTestCase):
    """Tests for the binary delimited separated values reader."""

    def testIterator(self):
        """Tests the iterator functionality."""
        test_file_path = self._GetTestFilePath(["password.csv"])
        self._SkipIfPathNotExists(test_file_path)

        resolver_context = context.Context()

        test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            test_path_spec, resolver_context=resolver_context
        )

        line_reader = line_reader_file.BinaryLineReader(file_object)

        dsv_reader = line_reader_file.BinaryDSVReader(line_reader, delimiter=b",")

        rows = []
        for row in dsv_reader:
            rows.append(row)

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0], [b"place", b"user", b"password"])
        self.assertEqual(rows[1], [b"bank", b"joesmith", b"superrich"])
        self.assertEqual(rows[2], [b"alarm system", b"-", b"1234"])
        self.assertEqual(rows[3], [b"treasure chest", b"-", b"1111"])
        self.assertEqual(rows[4], [b"uber secret laire", b"admin", b"admin"])


if __name__ == "__main__":
    unittest.main()
