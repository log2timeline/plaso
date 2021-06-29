#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YAML-based filter file."""

import io
import unittest

from plaso.engine import yaml_filter_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class YAMLFilterFileTest(shared_test_lib.BaseTestCase):
  """Tests for the YAML-based filter file."""

  # pylint: disable=protected-access

  def testReadFilterDefinition(self):
    """Tests the _ReadFilterDefinition function."""
    test_filter_file = yaml_filter_file.YAMLFilterFile()

    path_filter = test_filter_file._ReadFilterDefinition({
        'type': 'include', 'paths': ['/usr/bin']})

    self.assertIsNotNone(path_filter)
    self.assertIsNone(path_filter.description)
    self.assertEqual(path_filter.filter_type, 'include')
    self.assertEqual(path_filter.path_separator, '/')
    self.assertEqual(path_filter.paths, ['/usr/bin'])

    with self.assertRaises(errors.ParseError):
      test_filter_file._ReadFilterDefinition({})

    with self.assertRaises(errors.ParseError):
      test_filter_file._ReadFilterDefinition({'type': 'bogus'})

    with self.assertRaises(errors.ParseError):
      test_filter_file._ReadFilterDefinition({'type': 'include'})

    with self.assertRaises(errors.ParseError):
      test_filter_file._ReadFilterDefinition({'bogus': 'error'})

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['filter_files', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = yaml_filter_file.YAMLFilterFile()
    with io.open(test_file_path, 'r', encoding='utf-8') as file_object:
      path_filters = list(test_filter_file._ReadFromFileObject(file_object))

    self.assertEqual(len(path_filters), 3)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['filter_files', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = yaml_filter_file.YAMLFilterFile()
    path_filters = test_filter_file.ReadFromFile(test_file_path)

    self.assertEqual(len(path_filters), 3)

    self.assertEqual(path_filters[0].path_separator, '/')
    self.assertEqual(path_filters[0].paths, ['/usr/bin'])

    self.assertEqual(path_filters[1].path_separator, '\\')
    self.assertEqual(path_filters[1].paths, ['\\\\Windows\\\\System32'])


if __name__ == '__main__':
  unittest.main()
