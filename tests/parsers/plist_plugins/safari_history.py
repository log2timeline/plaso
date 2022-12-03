#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

from plaso.parsers.plist_plugins import safari_history

from tests.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'History.plist'

    plugin = safari_history.SafariHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 18)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'safari:history:visit',
        'last_visited_time': '2013-07-08T20:53:54.000000+00:00',
        'title': 'Amínósýrur',
        'url': 'http://netverslun.sci-mx.is/aminosyrur',
        'visit_count': 1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
