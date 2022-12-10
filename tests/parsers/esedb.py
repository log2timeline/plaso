#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Extensible Storage Engine (ESE) database files (EDB) parser."""

import unittest

from plaso.containers import warnings
from plaso.parsers import esedb
from plaso.parsers import esedb_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class ESEDBParserTest(test_lib.ParserTestCase):
  """Tests for the Extensible Storage Engine database (ESEDB) file parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = esedb.ESEDBParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

    parser.EnablePlugins(['file_history'])
    self.assertEqual(len(parser._plugins_per_name), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser = esedb.ESEDBParser()
    storage_writer = self._ParseFile(['Windows.edb'], parser)

    # Extensible Storage Engine Database information:
    #     File type:              Database
    #     Created in format:      0x620,17
    #     Current format:         0x620,17
    #     Page size:              32768 bytes

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = esedb.ESEDBParser()
    parser.ParseFileObject(parser_mediator, None)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    generator = storage_writer.GetAttributeContainers(
        warnings.ExtractionWarning.CONTAINER_TYPE)

    test_warnings = list(generator)
    test_warning = test_warnings[0]
    self.assertIsNotNone(test_warning)

    expected_message = 'unable to open file with error: Missing file object.'
    self.assertEqual(test_warning.message, expected_message)


if __name__ == '__main__':
  unittest.main()
