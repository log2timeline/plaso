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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2713)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'file_history:namespace:event',
        'file_attribute': 16,
        'identifier': 356,
        'original_filename': '?UP\\Favorites\\Links\\Lenovo',
        'parent_identifier': 230,
        'timestamp': '2013-10-12 17:34:36.688581',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'usn_number': 9251162904}

    self.CheckEventValues(storage_writer, events[702], expected_event_values)


if __name__ == '__main__':
  unittest.main()
