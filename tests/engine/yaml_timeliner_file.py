#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YAML-based timeliner configuration file."""

import io
import unittest

from plaso.engine import yaml_timeliner_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class YAMLTimelinerConfigurationFileTest(shared_test_lib.BaseTestCase):
  """Tests for the YAML-based timeliner configuration file."""

  # pylint: disable=protected-access

  _FORMATTERS_YAML = {
      'data_type': 'test:fs:stat',
      'attribute_mappings': [{
          'name': 'access_time',
          'description': 'Last Access Time'}],
      'place_holder_event': True}

  def testReadTimelinerDefinition(self):
    """Tests the _ReadTimelinerDefinition function."""
    test_timeliner_file = yaml_timeliner_file.YAMLTimelinerConfigurationFile()

    timeliner_definition = test_timeliner_file._ReadTimelinerDefinition(
        self._FORMATTERS_YAML)

    self.assertIsNotNone(timeliner_definition)
    self.assertEqual(timeliner_definition.data_type, 'test:fs:stat')

    with self.assertRaises(errors.ParseError):
      test_timeliner_file._ReadTimelinerDefinition({})

    with self.assertRaises(errors.ParseError):
      test_timeliner_file._ReadTimelinerDefinition({'bogus': 'error'})

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['timeliner.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_timeliner_file = yaml_timeliner_file.YAMLTimelinerConfigurationFile()

    with io.open(test_file_path, 'r', encoding='utf-8') as file_object:
      timeliner_definitions = list(test_timeliner_file._ReadFromFileObject(
          file_object))

    self.assertEqual(len(timeliner_definitions), 3)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['timeliner.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_timeliner_file = yaml_timeliner_file.YAMLTimelinerConfigurationFile()

    timeliner_definitions = list(test_timeliner_file.ReadFromFile(
        test_file_path))

    self.assertEqual(len(timeliner_definitions), 3)

    self.assertEqual(timeliner_definitions[0].data_type, 'test:fs:stat')


if __name__ == '__main__':
  unittest.main()
