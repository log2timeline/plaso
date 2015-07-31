#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MRUList Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mrulist

from tests.parsers.winreg_plugins import test_lib
from tests.winregistry import test_lib as winreg_test_lib


class TestMRUListStringPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the string MRUList plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulist.MRUListStringPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Microsoft\\Some Windows\\InterestingApp\\MRU'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        u'MRUList', u'acb'.encode(u'utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=123))
    values.append(winreg_test_lib.TestRegValue(
        u'a', u'Some random text here'.encode(u'utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1892))
    values.append(winreg_test_lib.TestRegValue(
        u'b', u'c:/evil.exe'.encode(u'utf_16_le'),
        winreg_test_lib.TestRegValue.REG_BINARY, offset=612))
    values.append(winreg_test_lib.TestRegValue(
        u'c', u'C:/looks_legit.exe'.encode(u'utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1001))

    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    winreg_key = winreg_test_lib.TestRegKey(
        key_path, timestamp, values, 1456)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value a]: Some random text here '
        u'Index: 2 [MRU Value c]: C:/looks_legit.exe '
        u'Index: 3 [MRU Value b]: c:/evil.exe').format(key_path)

    expected_msg_short = (
        u'[{0:s}] Index: 1 [MRU Value a]: Some ran...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class TestMRUListShellItemListPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the shell item list MRUList plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulist.MRUListShellItemListPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
        u'DesktopStreamMRU')
    values = []

    data = b''.join(map(chr, [
        0x14, 0x00, 0x1f, 0x00, 0xe0, 0x4f, 0xd0, 0x20, 0xea, 0x3a, 0x69, 0x10,
        0xa2, 0xd8, 0x08, 0x00, 0x2b, 0x30, 0x30, 0x9d, 0x19, 0x00, 0x23, 0x43,
        0x3a, 0x5c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x11, 0xee, 0x15, 0x00, 0x31,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x2e, 0x3e, 0x7a, 0x60, 0x10, 0x80, 0x57,
        0x69, 0x6e, 0x6e, 0x74, 0x00, 0x00, 0x18, 0x00, 0x31, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x50, 0x72, 0x6f, 0x66,
        0x69, 0x6c, 0x65, 0x73, 0x00, 0x00, 0x25, 0x00, 0x31, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x41, 0x64, 0x6d, 0x69,
        0x6e, 0x69, 0x73, 0x74, 0x72, 0x61, 0x74, 0x6f, 0x72, 0x00, 0x41, 0x44,
        0x4d, 0x49, 0x4e, 0x49, 0x7e, 0x31, 0x00, 0x17, 0x00, 0x31, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x44, 0x65, 0x73,
        0x6b, 0x74, 0x6f, 0x70, 0x00, 0x00, 0x00, 0x00]))

    values.append(winreg_test_lib.TestRegValue(
        u'MRUList', u'a'.encode(u'utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=123))
    values.append(winreg_test_lib.TestRegValue(
        u'a', data, winreg_test_lib.TestRegValue.REG_BINARY, offset=612))

    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    winreg_key = winreg_test_lib.TestRegKey(
        key_path, timestamp, values, 1456)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 5)

    # A MRUList event object.
    event_object = event_objects[4]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value a]: Shell item path: '
        u'<My Computer> C:\\Winnt\\Profiles\\Administrator\\Desktop').format(
            key_path)

    expected_msg_short = u'[{0:s}] Index:...'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A shell item event object.
    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-01-14 12:03:52')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Name: Winnt '
        u'Shell item path: <My Computer> C:\\Winnt '
        u'Origin: {0:s}').format(key_path)

    expected_msg_short = (
        u'Name: Winnt '
        u'Origin: \\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
        u'Deskt...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
