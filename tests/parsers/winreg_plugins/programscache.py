#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Explorer ProgramsCache Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import programcache

from tests.parsers.winreg_plugins import test_lib


class ExplorerProgramCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Explorer ProgramsCache Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = programcache.ExplorerProgramCachePlugin()

  def testProcessStartPage(self):
    """Tests the Process function on a StartPage key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
        u'StartPage')
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 0)

    # TODO: implement.

  def testProcessStartPage2(self):
    """Tests the Process function on a StartPage2 key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
        u'StartPage2')
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 0)

    # TODO: implement.


if __name__ == '__main__':
  unittest.main()
