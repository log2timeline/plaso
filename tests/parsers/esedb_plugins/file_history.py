#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the File History ESE database file."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import file_history as _  # pylint: disable=unused-import
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

    event = events[702]

    self.CheckTimestamp(event.timestamp, '2013-10-12 17:34:36.688581')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.usn_number, 9251162904)
    self.assertEqual(event_data.identifier, 356)

    filename = '?UP\\Favorites\\Links\\Lenovo'
    self.assertEqual(event_data.original_filename, filename)

    expected_message = (
        'Filename: {0:s} '
        'Identifier: 356 '
        'Parent Identifier: 230 '
        'Attributes: 16 '
        'USN number: 9251162904').format(filename)

    expected_short_message = 'Filename: {0:s}'.format(filename)

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
