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

    plugin_object = spotlight.SpotlightPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 9)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    expected_timestamps = [
        1375236414408299, 1376696381196456, 1379937262090906, 1380942616952359,
        1386111811136093, 1386951868185477, 1387822901900937, 1388331212005129,
        1389056477460443]
    timestamps = sorted([event_object.timestamp for event_object in events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = events[6]
    self.assertEqual(event_object.key, u'gr')
    self.assertEqual(event_object.root, u'/UserShortcuts')

    expected_description = (
        u'Spotlight term searched "gr" associate to Grab '
        u'(/Applications/Utilities/Grab.app)')
    self.assertEqual(event_object.desc, expected_description)

    expected_message = u'/UserShortcuts/gr {0:s}'.format(expected_description)
    expected_message_short = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
