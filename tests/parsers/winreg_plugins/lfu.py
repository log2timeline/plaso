#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import lfu
from plaso.winreg import cache

from tests.parsers.winreg_plugins import test_lib
from tests.winreg import test_lib as winreg_test_lib


class TestBootExecutePlugin(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootExecute Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry_cache = cache.WinRegistryCache()
    registry_cache.attributes[u'current_control_set'] = u'ControlSet001'
    self._plugin = lfu.BootExecutePlugin(reg_cache=registry_cache)

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\ControlSet001\\Control\\Session Manager'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        u'BootExecute', u'autocheck autochk *\x00'.encode(u'utf_16_le'),
        7, 123))
    values.append(winreg_test_lib.TestRegValue(
        u'CriticalSectionTimeout', u'2592000'.encode(u'utf_16_le'), 1, 153))
    values.append(winreg_test_lib.TestRegValue(
        u'ExcludeFromKnownDlls', u'\x00'.encode(u'utf_16_le'), 7, 163))
    values.append(winreg_test_lib.TestRegValue(
        u'GlobalFlag', u'0'.encode(u'utf_16_le'), 1, 173))
    values.append(winreg_test_lib.TestRegValue(
        u'HeapDeCommitFreeBlockThreshold', u'0'.encode(u'utf_16_le'), 1, 183))
    values.append(winreg_test_lib.TestRegValue(
        u'HeapDeCommitTotalFreeThreshold', u'0'.encode(u'utf_16_le'), 1, 203))
    values.append(winreg_test_lib.TestRegValue(
        u'HeapSegmentCommit', u'0'.encode(u'utf_16_le'), 1, 213))
    values.append(winreg_test_lib.TestRegValue(
        u'HeapSegmentReserve', u'0'.encode(u'utf_16_le'), 1, 223))
    values.append(winreg_test_lib.TestRegValue(
        u'NumberOfInitialSessions', u'2'.encode(u'utf_16_le'), 1, 243))

    timestamp = timelib.Timestamp.CopyFromString(u'2012-08-31 20:45:29')
    winreg_key = winreg_test_lib.TestRegKey(key_path, timestamp, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-31 20:45:29')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'[{0:s}] BootExecute: autocheck autochk *').format(key_path)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[1]

    expected_msg = (
        u'[{0:s}] '
        u'CriticalSectionTimeout: 2592000 '
        u'ExcludeFromKnownDlls: [] '
        u'GlobalFlag: 0 '
        u'HeapDeCommitFreeBlockThreshold: 0 '
        u'HeapDeCommitTotalFreeThreshold: 0 '
        u'HeapSegmentCommit: 0 '
        u'HeapSegmentReserve: 0 '
        u'NumberOfInitialSessions: 2').format(key_path)

    expected_msg_short = (
        u'[{0:s}] CriticalSectionTimeout: 2592000 Excl...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class TestBootVerificationRegistry(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootVerification Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry_cache = cache.WinRegistryCache()
    registry_cache.attributes[u'current_control_set'] = u'ControlSet001'
    self._plugin = lfu.BootVerificationPlugin(reg_cache=registry_cache)

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\ControlSet001\\Control\\BootVerificationProgram'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        u'ImagePath',
        u'C:\\WINDOWS\\system32\\googleupdater.exe'.encode(u'utf_16_le'),
        1, 123))

    timestamp = timelib.Timestamp.CopyFromString(u'2012-08-31 20:45:29')
    winreg_key = winreg_test_lib.TestRegKey(key_path, timestamp, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-31 20:45:29')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'ImagePath: C:\\WINDOWS\\system32\\googleupdater.exe').format(
            key_path)

    expected_msg_short = (
        u'[{0:s}] ImagePath: C:\\WINDOWS\\system...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
