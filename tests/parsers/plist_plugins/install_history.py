#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the install history plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import install_history

from tests.parsers.plist_plugins import test_lib


class InstallHistoryPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the install history plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = install_history.InstallHistoryPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'InstallHistory.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 7)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1384225175000000, 1388205491000000, 1388232883000000, 1388232883000000,
        1388232883000000, 1388232883000000, 1390941528000000])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[0]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/item')
    expected_desc = (
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
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/item/ {0:s}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
