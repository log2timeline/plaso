#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the spotlight plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers.plist_plugins import spotlight

from tests.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.spotlight.plist'

    plugin_object = spotlight.SpotlightPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 9)

    expected_timestamps = sorted([
        1379937262090906, 1387822901900937, 1375236414408299, 1388331212005129,
        1376696381196456, 1386951868185477, 1380942616952359, 1389056477460443,
        1386111811136093])
    timestamps = sorted([
        event_object.timestamp for event_object in storage_writer.events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = storage_writer.events[1]
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
