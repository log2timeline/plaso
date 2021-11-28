#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the install history plist plugin."""

import unittest

from plaso.parsers.plist_plugins import install_history

from tests.parsers.plist_plugins import test_lib


class InstallHistoryPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the install history plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'InstallHistory.plist'

    plugin = install_history.InstallHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1384225175000000, 1388205491000000, 1388232883000000, 1388232883000000,
        1388232883000000, 1388232883000000, 1390941528000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': (
            'Installation of [OS X 10.9 (13A603)] using [OS X Installer]. '
            'Packages: com.apple.pkg.BaseSystemBinaries, '
            'com.apple.pkg.BaseSystemResources, '
            'com.apple.pkg.Essentials, com.apple.pkg.BSD, '
            'com.apple.pkg.JavaTools, com.apple.pkg.AdditionalEssentials, '
            'com.apple.pkg.AdditionalSpeechVoices, '
            'com.apple.pkg.AsianLanguagesSupport, com.apple.pkg.MediaFiles, '
            'com.apple.pkg.JavaEssentials, com.apple.pkg.OxfordDictionaries, '
            'com.apple.pkg.X11redirect, com.apple.pkg.OSInstall, '
            'com.apple.pkg.update.compatibility.2013.001.'),
        'key': '',
        'root': '/item'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
