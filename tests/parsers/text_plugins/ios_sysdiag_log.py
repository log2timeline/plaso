#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Mobile Installation log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import ios_sysdiag_log

from tests.parsers.text_plugins import test_lib


class IOSSysdiagLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the iOS Mobile Installation log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = ios_sysdiag_log.IOSSysdiagLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['ios_sysdiag.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 28)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'Ignoring plugin at /System/Library/PrivateFrameworks/'
            'AccessibilityUtilities.framework/PlugIns/com.apple.accessibility.'
            'Accessibility.HearingAidsTapToRadar.appex due to validation '
            'issue(s). See previous log messages for details.'),
        'originating_call': (
            '+[MILaunchServicesDatabaseGatherer '
            'enumeratePluginKitPluginsInBundle:updatingPluginParentID:'
            'ensurePluginsAreExecutable:installProfiles:error:enumerator:]'),
        'process_identifier': 176,
        'severity': 'err',
        'written_time': '2021-08-11T05:51:02+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
