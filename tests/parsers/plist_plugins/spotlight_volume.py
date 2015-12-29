#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Spotlight Volume configuration plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import spotlight_volume

from tests.parsers.plist_plugins import test_lib


class SpotlightVolumePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight Volume configuration plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = spotlight_volume.SpotlightVolumePlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'VolumeConfiguration.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1372139683000000, 1369657656000000])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[0]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/Stores')
    expected_desc = (u'Spotlight Volume 4D4BFEB5-7FE6-4033-AAAA-'
                     u'AAAABBBBCCCCDDDD (/.MobileBackups) activated.')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/Stores/ {0:s}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
