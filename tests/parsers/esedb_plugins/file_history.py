#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the File History ESE database file."""

import unittest

from plaso.lib import definitions
from plaso.parsers.esedb_plugins import file_history

from tests.parsers.esedb_plugins import test_lib


class FileHistoryESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the File History ESE database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = file_history.FileHistoryESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(['Catalog1.edb'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2713)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'file_history:namespace:event',
        'date_time': '2013-10-12 17:34:36.6885806',
        'file_attribute': 16,
        'identifier': 356,
        'original_filename': '?UP\\Favorites\\Links\\Lenovo',
        'parent_identifier': 230,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'usn_number': 9251162904}

    self.CheckEventValues(storage_writer, events[702], expected_event_values)


if __name__ == '__main__':
  unittest.main()
