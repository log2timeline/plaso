#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.olecf_plugins import default

from tests import test_lib as shared_test_lib
from tests.parsers.olecf_plugins import test_lib


class TestDefaultPluginOLECF(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF default plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.doc'])
  def testProcess(self):
    """Tests the Process function."""
    plugin_object = default.DefaultOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'Document.doc'], plugin_object)

    self.assertEqual(len(storage_writer.events), 5)

    # Check the Root Entry event.
    event_object = storage_writer.events[0]

    self.assertEqual(event_object.name, u'Root Entry')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-05-16 02:29:49.795')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'Name: Root Entry')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Check one other entry.
    event_object = storage_writer.events[1]

    expected_string = u'Name: MsoDataStore'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-05-16 02:29:49.704')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
