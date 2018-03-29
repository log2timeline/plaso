#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the binary line reader file-like object."""

from __future__ import unicode_literals

import unittest

from dfvfs.file_io import os_file_io
from dfvfs.path import os_path_spec
from dfvfs.resolver import context

from plaso.lib import line_reader_file

from tests import test_lib as shared_test_lib


class BinaryLineReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the binary line reader."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._resolver_context = context.Context()

  @shared_test_lib.skipUnlessHasTestFile(['another_file'])
  def testReadline(self):
    """Test the readline() function."""
    test_file = self._GetTestFilePath(['another_file'])
    test_path_spec = os_path_spec.OSPathSpec(location=test_file)

    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_path_spec)
    line_reader = line_reader_file.BinaryLineReader(file_object)

    line = line_reader.readline()
    self.assertEqual(line, b'This is another file.\n')

    offset = line_reader.tell()
    self.assertEqual(offset, 22)

    line_reader = line_reader_file.BinaryLineReader(file_object)

    line = line_reader.readline(size=11)
    self.assertEqual(line, b'This is ano')

    offset = line_reader.tell()
    self.assertEqual(offset, 11)

    file_object.close()

  @shared_test_lib.skipUnlessHasTestFile(['password.csv'])
  def testReadlineMultipleLines(self):
    """Test the readline() function on multiple lines."""
    test_file = self._GetTestFilePath(['password.csv'])
    test_path_spec = os_path_spec.OSPathSpec(location=test_file)

    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_path_spec)
    line_reader = line_reader_file.BinaryLineReader(file_object)

    line = line_reader.readline()
    self.assertEqual(line, b'place,user,password\n')

    offset = line_reader.tell()
    self.assertEqual(offset, 20)

    line = line_reader.readline(size=5)
    self.assertEqual(line, b'bank,')

    offset = line_reader.tell()
    self.assertEqual(offset, 25)

    line = line_reader.readline()
    self.assertEqual(line, b'joesmith,superrich\n')

    offset = line_reader.tell()
    self.assertEqual(offset, 44)

    line = line_reader.readline()
    self.assertEqual(line, b'alarm system,-,1234\n')

    offset = line_reader.tell()
    self.assertEqual(offset, 64)

    file_object.close()

  @shared_test_lib.skipUnlessHasTestFile(['password.csv'])
  def testReadlines(self):
    """Test the readlines() function."""
    test_file = self._GetTestFilePath(['password.csv'])
    test_path_spec = os_path_spec.OSPathSpec(location=test_file)

    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_path_spec)
    line_reader = line_reader_file.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 5)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')
    self.assertEqual(lines[3], b'treasure chest,-,1111\n')
    self.assertEqual(lines[4], b'uber secret laire,admin,admin\n')

    file_object.close()

  @shared_test_lib.skipUnlessHasTestFile(['password.csv'])
  def testReadlinesWithSizeHint(self):
    """Test the readlines() function."""
    test_file = self._GetTestFilePath(['password.csv'])
    test_path_spec = os_path_spec.OSPathSpec(location=test_file)

    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_path_spec)
    line_reader = line_reader_file.BinaryLineReader(file_object)

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
    line_reader = line_reader_file.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 17)

  @shared_test_lib.skipUnlessHasTestFile(['password.csv'])
  def testIterator(self):
    """Test the iterator functionality."""
    test_file = self._GetTestFilePath(['password.csv'])
    test_path_spec = os_path_spec.OSPathSpec(location=test_file)

    file_object = os_file_io.OSFile(self._resolver_context)
    file_object.open(test_path_spec)
    line_reader = line_reader_file.BinaryLineReader(file_object)

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


if __name__ == '__main__':
  unittest.main()
