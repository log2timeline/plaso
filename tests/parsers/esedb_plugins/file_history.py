#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the File History ESE database file."""

import unittest

from plaso.parsers.esedb_plugins import file_history

from tests.parsers.esedb_plugins import test_lib


class FileHistoryESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the File History ESE database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = file_history.FileHistoryESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(['Catalog1.edb'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1373)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2013-09-02T20:02:25.6957745+00:00',
        'data_type': 'windows:file_history:namespace',
        'file_attribute': 16,
        'identifier': 356,
        'modification_time': '2013-10-12T17:34:36.6885806+00:00',
        'original_filename': '?UP\\Favorites\\Links\\Lenovo',
        'parent_identifier': 230,
        'usn_number': 9251162904}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 355)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
