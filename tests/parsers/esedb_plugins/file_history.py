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

    expected_filename = '?UP\\Favorites\\Links\\Lenovo'

    expected_event_values = {
        'identifier': 356,
        'original_filename': expected_filename,
        'timestamp': '2013-10-12 17:34:36.688581',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'usn_number': 9251162904}

    self.CheckEventValues(storage_writer, events[702], expected_event_values)

    expected_message = (
        'Filename: {0:s} '
        'Identifier: 356 '
        'Parent Identifier: 230 '
        'Attributes: 16 '
        'USN number: 9251162904').format(expected_filename)

    expected_short_message = 'Filename: {0:s}'.format(expected_filename)

    event_data = self._GetEventDataOfEvent(storage_writer, events[702])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
