#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Apple account plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import appleaccount
from plaso.parsers.plist_plugins import test_lib


class AppleAccountPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Apple account plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = appleaccount.AppleAccountPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_file = (
        u'com.apple.coreservices.appleidauthenticationinfo.'
        u'ABC0ABC1-ABC0-ABC0-ABC0-ABC0ABC1ABC2.plist')
    plist_name = plist_file
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 3)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1372106802000000, 1387980032000000, 1387980032000000])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[0]
    self.assertEqual(event_object.root, u'/Accounts')
    self.assertEqual(event_object.key, u'email@domain.com')
    expected_desc = (
        u'Configured Apple account email@domain.com (Joaquin Moreno Garijo)')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/Accounts/email@domain.com {0:s}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)

    event_object = event_objects[1]
    expected_desc = (
        u'Connected Apple account '
        u'email@domain.com (Joaquin Moreno Garijo)')
    self.assertEqual(event_object.desc, expected_desc)

    event_object = event_objects[2]
    expected_desc = (
        u'Last validation Apple account '
        u'email@domain.com (Joaquin Moreno Garijo)')
    self.assertEqual(event_object.desc, expected_desc)


if __name__ == '__main__':
  unittest.main()
