#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iPod plist plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.plist_plugins import ipod

from tests.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.iPod.plist'

    plugin = ipod.IPodPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'ipod:device:entry',
        'device_id': '0000A11300000000',
        'timestamp': '1995-11-22 18:25:07.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'ipod:device:entry',
        'device_class': 'iPhone',
        'device_id': '4C6F6F6E65000000',
        'family_id': 10016,
        'firmware_version': 256,
        'imei': '012345678901234',
        'serial_number': '526F676572',
        'timestamp': '2013-10-09 19:27:54.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_CONNECTED,
        'use_count': 1}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)


if __name__ == '__main__':
  unittest.main()
