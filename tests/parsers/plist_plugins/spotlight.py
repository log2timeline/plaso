#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the spotlight plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import spotlight

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.spotlight.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.spotlight.plist'

    plugin = spotlight.SpotlightPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 9)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375236414408299, 1376696381196456, 1379937262090906, 1380942616952359,
        1386111811136093, 1386951868185477, 1387822901900937, 1388331212005129,
        1389056477460443]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    event = events[6]
    self.assertEqual(event.key, u'gr')
    self.assertEqual(event.root, u'/UserShortcuts')

    expected_description = (
        u'Spotlight term searched "gr" associate to Grab '
        u'(/Applications/Utilities/Grab.app)')
    self.assertEqual(event.desc, expected_description)

    expected_message = u'/UserShortcuts/gr {0:s}'.format(expected_description)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
