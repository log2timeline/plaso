#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the install history plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 7)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1384225175000000, 1388205491000000, 1388232883000000, 1388232883000000,
        1388232883000000, 1388232883000000, 1390941528000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    event = events[0]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.key, '')
    self.assertEqual(event_data.root, '/item')

    expected_description = (
        'Installation of [OS X 10.9 (13A603)] using [OS X Installer]. '
        'Packages: com.apple.pkg.BaseSystemBinaries, '
        'com.apple.pkg.BaseSystemResources, '
        'com.apple.pkg.Essentials, com.apple.pkg.BSD, '
        'com.apple.pkg.JavaTools, com.apple.pkg.AdditionalEssentials, '
        'com.apple.pkg.AdditionalSpeechVoices, '
        'com.apple.pkg.AsianLanguagesSupport, com.apple.pkg.MediaFiles, '
        'com.apple.pkg.JavaEssentials, com.apple.pkg.OxfordDictionaries, '
        'com.apple.pkg.X11redirect, com.apple.pkg.OSInstall, '
        'com.apple.pkg.update.compatibility.2013.001.')
    self.assertEqual(event_data.desc, expected_description)

    expected_message = '/item/ {0:s}'.format(expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
