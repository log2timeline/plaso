#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS TimeMachine plist plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.plist_plugins import time_machine

from tests.parsers.plist_plugins import test_lib


class MacOSTimeMachinePlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS TimeMachine plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.TimeMachine.plist'

    plugin = time_machine.MacOSTimeMachinePlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 13)

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
        'backup_alias': 'BackUpFast',
        'data_type': 'macos:time_machine:backup',
        'date_time': '2013-09-25 08:40:55.000000',
        'destination_identifier': '5B33C22B-A4A1-4024-A2F5-C9979C4AAAAA',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
