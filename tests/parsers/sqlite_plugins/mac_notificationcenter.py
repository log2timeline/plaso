#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the MacOS Notification Center plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_notificationcenter

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacNotificationCenterTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Notification Center plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['mac_notificationcenter.db'])
  def testProcess(self):
    """Tests the Process function on a MacOS Notification Center db."""

    plugin = mac_notificationcenter.MacNotificationCenterPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_notificationcenter.db'], plugin)

    self.assertEqual(6, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    event = events[0]
    self.CheckTimestamp(event.timestamp, '2018-05-02 10:59:18.930156')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.body, "KeePassXC can now be run")
    self.assertEqual(event.bundle_name, "com.google.santagui")
    expected_message = (
        'Notification title "Santa" '
        ' '
        'registered by com.google.santagui.  '
        'Delivery status "1",  '
        'with the following content: "KeePassXC can now be run"')
    expected_short_message = (
        'Notification title "Santa"')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[2]
    self.CheckTimestamp(event.timestamp, '2018-05-02 11:13:21.531085')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.title, "Drive File Stream")
    self.assertEqual(event.bundle_name, "com.google.drivefs")
    expected_message = (
        'Notification title "Drive File Stream" '
        ' '
        'registered by com.google.drivefs.  '
        'Delivery status "1",  '
        'with the following content: "Drive File Stream is loading your'
        ' files…"')
    expected_short_message = (
        'Notification title "Drive File Stream"')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[5]
    self.CheckTimestamp(event.timestamp, '2018-05-16 16:38:04.686080')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.body, "PyCharm can now be run")
    self.assertEqual(event.bundle_name, "com.google.santagui")
    expected_message = (
        'Notification title "Santa" '
        ' '
        'registered by com.google.santagui.  '
        'Delivery status "1",  '
        'with the following content: "PyCharm can now be run"')
    expected_short_message = (
        'Notification title "Santa"')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

if __name__ == '__main__':
  unittest.main()
