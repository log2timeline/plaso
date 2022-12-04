#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the install history plist plugin."""

import unittest

from plaso.parsers.plist_plugins import install_history

from tests.parsers.plist_plugins import test_lib


class MacOSInstallHistoryPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the install history plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'InstallHistory.plist'

    plugin = install_history.MacOSInstallHistoryPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'macos:install_history:entry',
        'identifiers': [
            'com.apple.pkg.BaseSystemBinaries',
            'com.apple.pkg.BaseSystemResources',
            'com.apple.pkg.Essentials',
            'com.apple.pkg.BSD',
            'com.apple.pkg.JavaTools',
            'com.apple.pkg.AdditionalEssentials',
            'com.apple.pkg.AdditionalSpeechVoices',
            'com.apple.pkg.AsianLanguagesSupport',
            'com.apple.pkg.MediaFiles',
            'com.apple.pkg.JavaEssentials',
            'com.apple.pkg.OxfordDictionaries',
            'com.apple.pkg.X11redirect',
            'com.apple.pkg.OSInstall',
            'com.apple.pkg.update.compatibility.2013.001'],
        'name': 'OS X',
        'process_name': 'OS X Installer',
        'version': '10.9 (13A603)',
        'written_time': '2013-11-12T02:59:35.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
