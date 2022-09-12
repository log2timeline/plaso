#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spotlight searched terms plist plugin."""

import unittest

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'spotlight_searched_terms:entry',
        'date_time': '2013-12-23 18:21:41.900938',
        'display_name': 'Grab',
        'path': '/Applications/Utilities/Grab.app',
        'search_term': 'gr',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_USED}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
