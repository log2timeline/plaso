#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIE typed URLs Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import typedurls

from tests.parsers.winreg_plugins import test_lib


class MsieTypedURLsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MSIE typed URLs Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = typedurls.TypedURLsPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
        'TypedURLs')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\TypedPaths')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
        'TypedURLs')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = typedurls.TypedURLsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_entries = (
        'url1: http://cnn.com/ '
        'url2: http://twitter.com/ '
        'url3: http://linkedin.com/ '
        'url4: http://tweetdeck.com/ '
        'url5: mozilla '
        'url6: http://google.com/ '
        'url7: http://controller.shieldbase.local/certsrv/ '
        'url8: http://controller.shieldbase.local/ '
        'url9: http://www.stark-research-labs.com/ '
        'url10: http://www.adobe.com/ '
        'url11: http://www.google.com/ '
        'url12: http://www.firefox.com/ '
        'url13: http://go.microsoft.com/fwlink/?LinkId=69157')

    expected_event_values = {
        'data_type': 'windows:registry:typedurls',
        'entries': expected_entries,
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.plugin_name,
        'timestamp': '2012-03-12 21:23:53.307750'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


class TypedPathsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the typed paths Windows Registry plugin."""

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\TypedPaths')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = typedurls.TypedURLsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_entries = (
        'url1: \\\\controller')

    expected_event_values = {
        'data_type': 'windows:registry:typedurls',
        'entries': expected_entries,
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.plugin_name,
        'timestamp': '2010-11-10 07:58:15.811625'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
