#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

from plaso.formatters import msie_webcache  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.esedb_plugins import msie_webcache

from tests import test_lib as shared_test_lib
from tests.parsers.esedb_plugins import test_lib


class MsieWebCacheESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the MSIE WebCache ESE database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'WebCacheV01.dat'])
  def testProcess(self):
    """Tests the Process function."""
    plugin_object = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        [u'WebCacheV01.dat'], plugin_object)

    self.assertEqual(len(storage_writer.events), 1354)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    event_object = events[567]

    self.assertEqual(event_object.container_identifier, 1)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-12 07:30:25.486198')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_msg = (
        u'Container identifier: 1 '
        u'Set identifier: 0 '
        u'Name: Content '
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\ '
        u'Table: Container_1')
    expected_msg_short = (
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
