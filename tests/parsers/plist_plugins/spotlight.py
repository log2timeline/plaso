#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the spotlight plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import spotlight

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['com.apple.spotlight.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.spotlight.plist'

    plugin = spotlight.SpotlightPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_errors, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375236414408299, 1376696381196456, 1379937262090907, 1380942616952360,
        1386111811136094, 1386951868185478, 1387822901900938, 1388331212005130,
        1389056477460443]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    event = events[6]
    self.assertEqual(event.key, 'gr')
    self.assertEqual(event.root, '/UserShortcuts')

    expected_description = (
        'Spotlight term searched "gr" associate to Grab '
        '(/Applications/Utilities/Grab.app)')
    self.assertEqual(event.desc, expected_description)

    expected_message = '/UserShortcuts/gr {0:s}'.format(expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
