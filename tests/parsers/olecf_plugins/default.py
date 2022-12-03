#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

import unittest

from plaso.parsers.olecf_plugins import default

from tests.parsers.olecf_plugins import test_lib


class TestDefaultPluginOLECF(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF default plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = default.DefaultOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the Root Entry item.
    expected_event_values = {
        'data_type': 'olecf:item',
        'creation_time': None,
        'modification_time': '2013-05-16T02:29:49.7950000+00:00',
        'name': 'Root Entry'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check one other item.
    expected_event_values = {
        'data_type': 'olecf:item',
        'creation_time': '2013-05-16T02:29:49.7040000+00:00',
        'modification_time': '2013-05-16T02:29:49.7850000+00:00',
        'name': 'MsoDataStore'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
