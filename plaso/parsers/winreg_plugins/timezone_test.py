#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the timezone Windows Registry plugin."""

import unittest

from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import timezone as winreg_timezone
from plaso.winreg import test_lib as winreg_test_lib


class WinRegTimezonePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the timezone Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winreg_timezone.WinRegTimezonePlugin()

  def testProcessMock(self):
    """Tests the Process function on created key."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    key_path = u'\\ControlSet001\\Control\\TimeZoneInformation'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'ActiveTimeBias', '\xFF\xFF\xFF\xC4',
        winreg_test_lib.TestRegValue.REG_DWORD_BIG_ENDIAN))

    values.append(winreg_test_lib.TestRegValue(
        'Bias', '\xFF\xFF\xFF\xC4',
        winreg_test_lib.TestRegValue.REG_DWORD_BIG_ENDIAN))

    values.append(winreg_test_lib.TestRegValue(
        'DaylightBias', '\xFF\xFF\xFF\xC4',
        winreg_test_lib.TestRegValue.REG_DWORD_BIG_ENDIAN))

    values.append(winreg_test_lib.TestRegValue(
        'DaylightName', '@tzres.dll,-321'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ))

    values.append(winreg_test_lib.TestRegValue(
        'DaylightStart', '\x00\x00\x03\x00\x05\x00\x02\x00'
        '\x00\x00\x00\x00\x00\x00\x00\x00',
        winreg_test_lib.TestRegValue.REG_BINARY))

    values.append(winreg_test_lib.TestRegValue(
        'DynamicDaylightTimeDisabled', '\x00\x00\x00\x00',
        winreg_test_lib.TestRegValue.REG_DWORD_BIG_ENDIAN))

    values.append(winreg_test_lib.TestRegValue(
        'StandardBias', '\x00\x00\x00\x00',
        winreg_test_lib.TestRegValue.REG_DWORD_BIG_ENDIAN))

    values.append(winreg_test_lib.TestRegValue(
        'StandardName', '@tzres.dll,-322'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ))

    values.append(winreg_test_lib.TestRegValue(
        'StandardStart', '\x00\x00\x0A\x00\x05\x00\x03\x00'
        '\x00\x00\x00\x00\x00\x00\x00\x00',
        winreg_test_lib.TestRegValue.REG_BINARY))

    values.append(winreg_test_lib.TestRegValue(
        'TimeZoneKeyName', 'W. Europe Standard Time'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ))

    # expr `date -u -d "2013-01-30 10:47:57" +"%s%N"` \/ 1000
    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1359542877000000, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-01-30 10:47:57.000000')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'ActiveTimeBias: -60 '
        u'Bias: -60 '
        u'DaylightBias: -60 '
        u'DaylightName: @tzres.dll,-321 '
        u'DynamicDaylightTimeDisabled: 0 '
        u'StandardBias: 0 '
        u'StandardName: @tzres.dll,-322 '
        u'TimeZoneKeyName: W. Europe Standard Time').format(key_path)

    expected_msg_short = (
        u'[{0:s}] '
        u'ActiveTimeBias: -60 '
        u'Bias: -60 '
        u'Da...').format(key_path)

    self._TestGetMessageStrings(
        event_objects[0], expected_msg, expected_msg_short)

  def testProcessFile(self):
    """Tests the Process function on registry file."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath(['SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\TimeZoneInformation'
    winreg_key = self._GetKeyFromFile(test_file, key_path)

    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-03-11 07:00:00.000642')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'ActiveTimeBias: 240 '
        u'Bias: 300 '
        u'DaylightBias: -60 '
        u'DaylightName: @tzres.dll,-111 '
        u'DynamicDaylightTimeDisabled: 0 '
        u'StandardBias: 0 '
        u'StandardName: @tzres.dll,-112 '
        u'TimeZoneKeyName: Eastern Standard Time').format(key_path)

    expected_msg_short = (
        u'[{0:s}] '
        u'ActiveTimeBias: 240 '
        u'Bias: 300 '
        u'Da...').format(key_path)

    self._TestGetMessageStrings(
        event_objects[0], expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
