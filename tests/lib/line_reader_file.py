#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the binary line reader file-like object."""

import unittest

from dfvfs.path import os_path_spec
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import line_reader_file

from tests import test_lib as shared_test_lib


class BinaryLineReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the binary line reader."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._resolver_context = context.Context()

  def testReadline(self):
    """Test the readline() function."""
    test_file_path = self._GetTestFilePath(['another_file'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

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

  def testReadlineMultipleLines(self):
    """Test the readline() function on multiple lines."""
    test_file_path = self._GetTestFilePath(['password.csv'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

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

  def testReadlines(self):
    """Test the readlines() function."""
    test_file_path = self._GetTestFilePath(['password.csv'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

    line_reader = line_reader_file.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 5)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')
    self.assertEqual(lines[3], b'treasure chest,-,1111\n')
    self.assertEqual(lines[4], b'uber secret laire,admin,admin\n')

  def testReadlinesWithSizeHint(self):
    """Test the readlines() function."""
    test_file_path = self._GetTestFilePath(['password.csv'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

    line_reader = line_reader_file.BinaryLineReader(file_object)

    lines = line_reader.readlines(sizehint=60)

    self.assertEqual(len(lines), 3)
    self.assertEqual(lines[0], b'place,user,password\n')
    self.assertEqual(lines[1], b'bank,joesmith,superrich\n')
    self.assertEqual(lines[2], b'alarm system,-,1234\n')

  def testReadlinesWithFileWithoutNewLineAtEnd(self):
    """Test reading lines from a file without a new line char at the end."""
    test_file_path = self._GetTestFilePath(['bodyfile'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

    line_reader = line_reader_file.BinaryLineReader(file_object)

    lines = line_reader.readlines()

    self.assertEqual(len(lines), 25)

  def testIterator(self):
    """Test the iterator functionality."""
    test_file_path = self._GetTestFilePath(['password.csv'])
    self._SkipIfPathNotExists(test_file_path)

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=self._resolver_context)

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

  # TODO: Add a test which tests reading a file which is
  # larger than the buffer size, and read lines until it crosses
  # that original buffer size (to test if the buffer is correctly
  # filled).


class BinaryDSVReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the binary delimited separated values reader."""

  def testIterator(self):
    """Tests the iterator functionality."""
    test_file_path = self._GetTestFilePath(['password.csv'])
    self._SkipIfPathNotExists(test_file_path)

    resolver_context = context.Context()

    test_path_spec = os_path_spec.OSPathSpec(location=test_file_path)
    file_object = path_spec_resolver.Resolver.OpenFileObject(
        test_path_spec, resolver_context=resolver_context)

    line_reader = line_reader_file.BinaryLineReader(file_object)

    dsv_reader = line_reader_file.BinaryDSVReader(line_reader, delimiter=b',')

    rows = []
    for row in dsv_reader:
      rows.append(row)

    self.assertEqual(len(rows), 5)
    self.assertEqual(rows[0], [b'place', b'user', b'password'])
    self.assertEqual(rows[1], [b'bank', b'joesmith', b'superrich'])
    self.assertEqual(rows[2], [b'alarm system', b'-', b'1234'])
    self.assertEqual(rows[3], [b'treasure chest', b'-', b'1111'])
    self.assertEqual(rows[4], [b'uber secret laire', b'admin', b'admin'])


if __name__ == '__main__':
  unittest.main()
