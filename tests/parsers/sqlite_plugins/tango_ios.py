# -*- coding: utf-8 -*-
"""Test for Tango IOS plugin."""

import unittest

from plaso.parsers.sqlite_plugins import tango_ios

from tests.parsers.sqlite_plugins import test_lib

class TangoIOSTest(test_lib.SQLitePluginTestCase):
  """Test for the Tango IOS plugin."""

  def testProcess(self):
    """Tests the process method."""
    test_file = self._GetTestFilePath([u'tc.db'])
    plugin = tango_ios.TangoIOSPlugin()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    test_event = event_objects[0]
    self.assertIsInstance(test_event, tango_ios.TangoIOSMessageSentEvent)


if __name__ == '__main__':
  unittest.main()