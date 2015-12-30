#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the File History ESE database file."""

import unittest

from plaso.formatters import file_history as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.esedb_plugins import file_history

from tests.parsers.esedb_plugins import test_lib


class FileHistoryEseDbPluginTest(test_lib.EseDbPluginTestCase):
  """Tests for the File History ESE database plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = file_history.FileHistoryEseDbPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_name = u'Catalog1.edb'
    event_queue_consumer = self._ParseEseDbFileWithPlugin(
        [test_file_name], self._plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2680)

    event_object = event_objects[693]

    self.assertEqual(event_object.usn_number, 9251162904)
    self.assertEqual(event_object.identifier, 356)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-12 17:34:36.688580')

    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    filename = u'?UP\\Favorites\\Links\\Lenovo'
    self.assertEqual(event_object.original_filename, filename)

    expected_msg = (
        u'Filename: {0:s} Identifier: 356 Parent Identifier: 230 Attributes: '
        u'16 USN number: 9251162904').format(filename)

    expected_msg_short = u'Filename: {0:s}'.format(filename)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
