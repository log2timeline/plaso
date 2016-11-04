#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the install history plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import install_history

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class InstallHistoryPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the install history plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'InstallHistory.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'InstallHistory.plist'

    plugin_object = install_history.InstallHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 7)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    expected_timestamps = [
        1384225175000000, 1388205491000000, 1388232883000000, 1388232883000000,
        1388232883000000, 1388232883000000, 1390941528000000]
    timestamps = sorted([event_object.timestamp for event_object in events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = events[0]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/item')

    expected_description = (
        u'Installation of [OS X 10.9 (13A603)] using [OS X Installer]. '
        u'Packages: com.apple.pkg.BaseSystemBinaries, '
        u'com.apple.pkg.BaseSystemResources, '
        u'com.apple.pkg.Essentials, com.apple.pkg.BSD, '
        u'com.apple.pkg.JavaTools, com.apple.pkg.AdditionalEssentials, '
        u'com.apple.pkg.AdditionalSpeechVoices, '
        u'com.apple.pkg.AsianLanguagesSupport, com.apple.pkg.MediaFiles, '
        u'com.apple.pkg.JavaEssentials, com.apple.pkg.OxfordDictionaries, '
        u'com.apple.pkg.X11redirect, com.apple.pkg.OSInstall, '
        u'com.apple.pkg.update.compatibility.2013.001.')
    self.assertEqual(event_object.desc, expected_description)

    expected_message = u'/item/ {0:s}'.format(expected_description)
    expected_message_short = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
