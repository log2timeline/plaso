#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS TimeMachine plist plugin."""

import unittest

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'backup_alias': 'BackUpFast',
        'data_type': 'macos:time_machine:backup',
        'destination_identifier': '5B33C22B-A4A1-4024-A2F5-C9979C4AAAAA',
        'snapshot_times': [
            '2013-09-14T13:24:11.000000+00:00',
            '2013-09-25T08:40:55.000000+00:00',
            '2013-10-03T14:24:36.000000+00:00',
            '2013-10-16T00:32:18.000000+00:00',
            '2013-10-24T20:51:30.000000+00:00',
            '2013-11-02T00:22:19.000000+00:00',
            '2013-11-10T13:27:00.000000+00:00',
            '2013-11-22T14:35:14.000000+00:00',
            '2013-12-05T17:51:51.000000+00:00',
            '2013-12-10T15:37:32.000000+00:00',
            '2013-12-22T14:38:11.000000+00:00',
            '2014-01-04T13:09:10.000000+00:00',
            '2014-01-04T13:38:38.000000+00:00']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
