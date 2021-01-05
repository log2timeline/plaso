#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the filter file."""

import io
import unittest

from plaso.engine import filter_file

from tests import test_lib as shared_test_lib


class FilterFileTestCase(shared_test_lib.BaseTestCase):
  """Tests for the filter file."""

  # pylint: disable=protected-access

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['filter_files', 'format_test.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = filter_file.FilterFile()
    with io.open(test_file_path, 'r', encoding='utf-8') as file_object:
      path_filters = list(test_filter_file._ReadFromFileObject(file_object))

    self.assertEqual(len(path_filters), 1)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['filter_files', 'format_test.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = filter_file.FilterFile()
    path_filters = test_filter_file.ReadFromFile(test_file_path)

    self.assertEqual(len(path_filters), 1)

    self.assertEqual(path_filters[0].path_separator, '/')
    self.assertEqual(path_filters[0].paths, ['/usr/bin', '/Windows/System32'])


if __name__ == '__main__':
  unittest.main()
