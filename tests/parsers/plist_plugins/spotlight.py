#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the spotlight plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import spotlight

from tests.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = spotlight.SpotlightPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.spotlight.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 9)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1379937262090906, 1387822901900937, 1375236414408299, 1388331212005129,
        1376696381196456, 1386951868185477, 1380942616952359, 1389056477460443,
        1386111811136093])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[6]
    self.assertEqual(event_object.key, u'gr')
    self.assertEqual(event_object.root, u'/UserShortcuts')
    expected_desc = (u'Spotlight term searched "gr" associate to '
                     u'Grab (/Applications/Utilities/Grab.app)')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/UserShortcuts/gr {0:s}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
