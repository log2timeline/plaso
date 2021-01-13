#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

from plaso.parsers.plist_plugins import softwareupdate

from tests.parsers.plist_plugins import test_lib


class SoftwareUpdatePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.SoftwareUpdate.plist'

    plugin = softwareupdate.SoftwareUpdatePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': (
            'Last Mac OS 10.9.1 (13B42) partially '
            'update, pending 1: RAWCameraUpdate5.03(031-2664).'),
        'key': '',
        'root': '/',
        'timestamp': '2014-01-06 17:43:48.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': 'Last MacOS 10.9.1 (13B42) full update.',
        'key': '',
        'root': '/',
        'timestamp': '2014-01-06 17:43:48.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
