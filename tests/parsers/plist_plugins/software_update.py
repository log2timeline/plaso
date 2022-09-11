#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.plist_plugins import software_update

from tests.parsers.plist_plugins import test_lib


class MacOSSoftwareUpdatePlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.SoftwareUpdate.plist'

    plugin = software_update.MacOSSoftwareUpdatePlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

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
        'data_type': 'macos:software_updata:entry',
        'date_time': '2014-01-06 17:43:48.000000',
        'recommended_updates': ['RAWCameraUpdate5.03 (031-2664)'],
        'system_version': '10.9.1 (13B42)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UPDATE}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
