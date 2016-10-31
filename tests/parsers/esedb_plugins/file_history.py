#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the File History ESE database file."""

import unittest

from plaso.formatters import file_history  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.esedb_plugins import file_history

from tests import test_lib as shared_test_lib
from tests.parsers.esedb_plugins import test_lib


class FileHistoryESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the File History ESE database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Catalog1.edb'])
  def testProcess(self):
    """Tests the Process function."""
    plugin_object = file_history.FileHistoryESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        [u'Catalog1.edb'], plugin_object)

    self.assertEqual(len(storage_writer.events), 2680)

    event_object = storage_writer.events[693]

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
