#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

from plaso.parsers.plist_plugins import safari

from tests.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'History.plist'

    plugin = safari.SafariHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 18)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'safari:history:visit',
        'timestamp': '2013-07-08 17:31:00.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'data_type': 'safari:history:visit',
        'title': 'Amínósýrur',
        'url': 'http://netverslun.sci-mx.is/aminosyrur',
        'visit_count': 1}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
