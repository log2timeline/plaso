#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spotlight Volume configuration plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import spotlight_volume

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SpotlightVolumePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight Volume configuration plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['VolumeConfiguration.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'VolumeConfiguration.plist'

    plugin = spotlight_volume.SpotlightVolumePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [1369657656000000, 1372139683000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    event = events[1]

    self.assertEqual(event.key, '')
    self.assertEqual(event.root, '/Stores')

    expected_description = (
        'Spotlight Volume 4D4BFEB5-7FE6-4033-AAAA-AAAABBBBCCCCDDDD '
        '(/.MobileBackups) activated.')
    self.assertEqual(event.desc, expected_description)

    expected_message = '/Stores/ {0:s}'.format(expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
