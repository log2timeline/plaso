#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spotlight searched terms plist plugin."""

import unittest

from plaso.parsers.plist_plugins import spotlight_searched_terms

from tests.parsers.plist_plugins import test_lib


class SpotlightSearchedTermsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight searched terms plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.spotlight.plist'

    plugin = spotlight_searched_terms.SpotlightSearchedTermsPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'spotlight_searched_terms:entry',
        'display_name': 'Grab',
        'last_used_time': '2013-12-23T18:21:41.900938+00:00',
        'path': '/Applications/Utilities/Grab.app',
        'search_term': 'gr'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
