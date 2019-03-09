#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the MacOS Notification Center plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_knowledgec

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacKnowledgecTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Notification Center plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['mac_knowledgec.db'])
  def testProcess(self):
    """Tests the Process function on a MacOS KnowledgeC db."""

    plugin = mac_knowledgec.MacKnowledgeCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec.db'], plugin)

    self.assertEqual(6, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    event = events[0]
    self.CheckTimestamp(event.timestamp, '2018-05-02 10:59:18.930156')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.body, "KeePassXC can now be run")
    self.assertEqual(event.bundle_name, "com.google.santagui")
    expected_short_message = (
        'Title: Santa, Content: KeePassXC can now be run')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
