#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Spotlight Volume configuration plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import spotlight_volume

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SpotlightVolumePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight Volume configuration plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'VolumeConfiguration.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'VolumeConfiguration.plist'

    plugin_object = spotlight_volume.SpotlightVolumePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    expected_timestamps = [1369657656000000, 1372139683000000]
    timestamps = sorted([event_object.timestamp for event_object in events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = events[1]

    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/Stores')

    expected_description = (
        u'Spotlight Volume 4D4BFEB5-7FE6-4033-AAAA-AAAABBBBCCCCDDDD '
        u'(/.MobileBackups) activated.')
    self.assertEqual(event_object.desc, expected_description)

    expected_message = u'/Stores/ {0:s}'.format(expected_description)
    expected_message_short = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
