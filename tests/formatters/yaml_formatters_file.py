#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YAML-based formatters file."""

from __future__ import unicode_literals

import io
import unittest

from plaso.formatters import yaml_formatters_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class YAMLFormattersFileTest(shared_test_lib.BaseTestCase):
  """Tests for the YAML-based formatters file."""

  # pylint: disable=protected-access

  def testReadFormatterDefinition(self):
    """Tests the _ReadFormatterDefinition function."""
    test_formatters_file = yaml_formatters_file.YAMLFormattersFile()

    formatter = test_formatters_file._ReadFormatterDefinition({
        'type': 'conditional',
        'data_type': 'fs:stat',
        'message': [
            '{display_name}',
            'Type: {file_entry_type}',
            '({unallocated})'],
        'short_message': [
            '{filename}'],
        'short_source': 'FILE',
        'source': 'File system'})

    self.assertIsNotNone(formatter)
    self.assertEqual(formatter.DATA_TYPE, 'fs:stat')

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({'type': 'bogus'})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({'type': 'conditional'})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({
          'type': 'conditional',
          'data_type': 'fs:stat'})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({
          'type': 'conditional',
          'data_type': 'fs:stat',
          'message': [
              '{display_name}',
              'Type: {file_entry_type}',
              '({unallocated})']})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({
          'type': 'conditional',
          'data_type': 'fs:stat',
          'message': [
              '{display_name}',
              'Type: {file_entry_type}',
              '({unallocated})'],
          'short_message': [
              '{filename}']})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({
          'type': 'conditional',
          'data_type': 'fs:stat',
          'message': [
              '{display_name}',
              'Type: {file_entry_type}',
              '({unallocated})'],
          'short_message': [
              '{filename}'],
          'short_source': 'FILE'})

    with self.assertRaises(errors.ParseError):
      test_formatters_file._ReadFormatterDefinition({'bogus': 'error'})

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_formatters_file = yaml_formatters_file.YAMLFormattersFile()

    with io.open(test_file_path, 'r', encoding='utf-8') as file_object:
      formatters = list(test_formatters_file._ReadFromFileObject(file_object))

    self.assertEqual(len(formatters), 1)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_formatters_file = yaml_formatters_file.YAMLFormattersFile()

    formatters = test_formatters_file.ReadFromFile(test_file_path)

    self.assertEqual(len(formatters), 1)

    self.assertEqual(formatters[0].DATA_TYPE, 'fs:stat')


if __name__ == '__main__':
  unittest.main()
