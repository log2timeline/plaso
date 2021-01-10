#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple account plist plugin."""

import unittest

from plaso.parsers.plist_plugins import appleaccount

from tests.parsers.plist_plugins import test_lib


class AppleAccountPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Apple account plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_file = (
        'com.apple.coreservices.appleidauthenticationinfo.'
        'ABC0ABC1-ABC0-ABC0-ABC0-ABC0ABC1ABC2.plist')
    plist_name = plist_file

    plugin = appleaccount.AppleAccountPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [1372106802000000, 1387980032000000, 1387980032000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    expected_description = (
        'Configured Apple account email@domain.com (Joaquin Moreno Garijo)')

    expected_event_values = {
        'desc': expected_description,
        'key': 'email@domain.com',
        'root': '/Accounts'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = '/Accounts/email@domain.com {0:s}'.format(
        expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'desc': (
            'Connected Apple account '
            'email@domain.com (Joaquin Moreno Garijo)')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'desc': (
            'Last validation Apple account '
            'email@domain.com (Joaquin Moreno Garijo)')}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)


if __name__ == '__main__':
  unittest.main()
