#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound Files (OLECF) parser."""

import unittest

from plaso.containers import warnings
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers import olecf_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class OLECFParserTest(test_lib.ParserTestCase):
  """Tests for the OLE Compound Files (OLECF) parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = olecf.OLECFParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    # Extract 1 for the default plugin.
    self.assertEqual(len(parser._plugins), number_of_plugins - 1)

    parser.EnablePlugins(['olecf_document_summary'])
    self.assertEqual(len(parser._plugins), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser = olecf.OLECFParser()
    storage_writer = self._ParseFile(['Document.doc'], parser)

    # OLE Compound File information:
    #     Version             : 3.62
    #     Sector size         : 512
    #     Short sector size   : 64

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'olecf:item',
        'date_time': '2013-05-16 02:29:49.7850000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    parser = olecf.OLECFParser()
    parser.ParseFileObject(parser_mediator, None)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 0)

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

    expected_message = (
        'unable to open file with error: pyolecf_file_open_file_object: ')
    self.assertTrue(test_warning.message.startswith(expected_message))


if __name__ == '__main__':
  unittest.main()
