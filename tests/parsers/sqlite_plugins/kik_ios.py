#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Kik messenger plugin."""

import unittest

from plaso.formatters import kik_ios  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import kik_ios

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class KikMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the Kik message database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'kik_ios.sqlite'])
  def testProcess(self):
    """Test the Process function on a Kik messenger kik.sqlite file."""
    plugin_object = kik_ios.KikIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'kik_ios.sqlite'], plugin_object)

    # The Kik database file contains 60 events.
    self.assertEqual(len(storage_writer.events), 60)

    # Check the second message sent.
    event_object = storage_writer.events[1]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-06-29 12:26:11.000')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_username = u'ken.doh'
    self.assertEqual(event_object.username, expected_username)

    expected_displayname = u'Ken Doh'
    self.assertEqual(event_object.displayname, expected_displayname)

    expected_body = u'Hello'
    self.assertEqual(event_object.body, expected_body)

    expected_msg = (
        u'Username: ken.doh '
        u'Displayname: Ken Doh '
        u'Status: read after offline '
        u'Type: sent '
        u'Message: Hello')
    expected_short = u'Hello'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
