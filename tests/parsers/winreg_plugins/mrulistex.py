#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MRUListEx Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mrulistex

from tests.parsers.winreg_plugins import test_lib


class TestMRUListExStringPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the string MRUListEx plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulistex.MRUListExStringPlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_fake.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'MRUlist', key_path=key_path,
        last_written_time=filetime.timestamp, offset=1456)

    # The order is: 201
    value_data = b'\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRUListEx', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY, offset=123)
    registry_key.AddValue(registry_value)

    value_data = u'Some random text here'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'0', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = u'c:\\evil.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'1', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = u'C:\\looks_legit.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'2', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1001)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Microsoft\\Some Windows\\InterestingApp\\MRUlist'
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    # A MRUListEx event object.
    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 2]: C:\\looks_legit.exe '
        u'Index: 2 [MRU Value 0]: Some random text here '
        u'Index: 3 [MRU Value 1]: c:\\evil.exe').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TestMRUListExShellItemListPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the shell item list MRUListEx plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulistex.MRUListExShellItemListPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
        u'OpenSavePidlMRU')
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 65)

    # A MRUListEx event object.
    event_object = event_objects[40]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-08-28 22:48:28.159308')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}\\exe] '
        u'Index: 1 [MRU Value 1]: Shell item path: <My Computer> '
        u'P:\\Application Tools\\Firefox 6.0\\Firefox Setup 6.0.exe '
        u'Index: 2 [MRU Value 0]: Shell item path: <Computers and Devices> '
        u'<UNKNOWN: 0x00>\\\\controller\\WebDavShare\\Firefox Setup 3.6.12.exe'
        u'').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # A shell item event object.
    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-08 22:16:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'Name: ALLOYR~1 '
        u'Long name: Alloy Research '
        u'NTFS file reference: 44518-33 '
        u'Shell item path: <Shared Documents Folder (Users Files)> '
        u'<UNKNOWN: 0x00>\\Alloy Research '
        u'Origin: {0:s}\\*').format(key_path)
    expected_short_message = (
        u'Name: Alloy Research '
        u'NTFS file reference: 44518-33 '
        u'Origin: \\Software\\Microsof...')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TestMRUListExStringAndShellItemPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the string and shell item MRUListEx plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulistex.MRUListExStringAndShellItemPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs')
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    # A MRUListEx event object.
    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-01 13:52:39.113741')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 17]: Path: The SHIELD, '
        u'Shell item: [The SHIELD.lnk] '
        u'Index: 10 [MRU Value 11]: Path: 5031RR_BalancedLeadership.pdf, '
        u'Shell item: [5031RR_BalancedLeadership.lnk] '
        u'Index: 11 [MRU Value 10]: '
        u'Path: SA-23E Mitchell-Hyundyne Starfury.docx, '
        u'Shell item: [SA-23E Mitchell-Hyundyne Starfury.lnk] '
        u'Index: 12 [MRU Value 9]: Path: StarFury.docx, '
        u'Shell item: [StarFury (3).lnk] '
        u'Index: 13 [MRU Value 6]: Path: StarFury.zip, '
        u'Shell item: [StarFury.lnk] '
        u'Index: 14 [MRU Value 4]: Path: VIBRANIUM.docx, '
        u'Shell item: [VIBRANIUM.lnk] '
        u'Index: 15 [MRU Value 5]: Path: ADAMANTIUM-Background.docx, '
        u'Shell item: [ADAMANTIUM-Background.lnk] '
        u'Index: 16 [MRU Value 3]: Path: Pictures, '
        u'Shell item: [Pictures.lnk] '
        u'Index: 17 [MRU Value 2]: Path: nick_fury_77831.jpg, '
        u'Shell item: [nick_fury_77831.lnk] '
        u'Index: 18 [MRU Value 1]: Path: Downloads, '
        u'Shell item: [Downloads.lnk] '
        u'Index: 19 [MRU Value 0]: Path: wallpaper_medium.jpg, '
        u'Shell item: [wallpaper_medium.lnk] '
        u'Index: 2 [MRU Value 18]: '
        u'Path: captain_america_shield_by_almogrem-d48x9x8.jpg, '
        u'Shell item: [captain_america_shield_by_almogrem-d48x9x8.lnk] '
        u'Index: 3 [MRU Value 16]: Path: captain-america-shield-front.jpg, '
        u'Shell item: [captain-america-shield-front.lnk] '
        u'Index: 4 [MRU Value 12]: Path: Leadership, '
        u'Shell item: [Leadership.lnk] '
        u'Index: 5 [MRU Value 15]: Path: followership.pdf, '
        u'Shell item: [followership.lnk] '
        u'Index: 6 [MRU Value 14]: Path: leaderqualities.pdf, '
        u'Shell item: [leaderqualities.lnk] '
        u'Index: 7 [MRU Value 13]: Path: htlhtl.pdf, '
        u'Shell item: [htlhtl.lnk] '
        u'Index: 8 [MRU Value 8]: Path: StarFury, '
        u'Shell item: [StarFury (2).lnk] '
        u'Index: 9 [MRU Value 7]: Path: Earth_SA-26_Thunderbolt.jpg, '
        u'Shell item: [Earth_SA-26_Thunderbolt.lnk]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TestMRUListExStringAndShellItemListPlugin(
    test_lib.RegistryPluginTestCase):
  """Tests for the string and shell item list MRUListEx plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulistex.MRUListExStringAndShellItemListPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
        u'LastVisitedPidlMRU')
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 31)

    # A MRUListEx event object.
    event_object = event_objects[30]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-01 13:52:38.966290')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 1]: Path: chrome.exe, '
        u'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        u'<UNKNOWN: 0x00> '
        u'Index: 2 [MRU Value 7]: '
        u'Path: {{48E1ED6B-CF49-4609-B1C1-C082BFC3D0B4}}, '
        u'Shell item path: <Shared Documents Folder (Users Files)> '
        u'<UNKNOWN: 0x00>\\Alloy Research '
        u'Index: 3 [MRU Value 6]: '
        u'Path: {{427865A0-03AF-4F25-82EE-10B6CB1DED3E}}, '
        u'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        u'Index: 4 [MRU Value 5]: '
        u'Path: {{24B5C9BB-48B5-47FF-8343-40481DBA1E2B}}, '
        u'Shell item path: <My Computer> C:\\Users\\nfury\\Documents '
        u'Index: 5 [MRU Value 4]: '
        u'Path: {{0B8CFE96-DB69-4D33-8E3C-36EAB4F709E0}}, '
        u'Shell item path: <My Computer> C:\\Users\\nfury\\Documents\\'
        u'Alloy Research '
        u'Index: 6 [MRU Value 3]: '
        u'Path: {{D4F85F66-003D-4127-BCE9-CAD7A57B2857}}, '
        u'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        u'Index: 7 [MRU Value 0]: Path: iexplore.exe, '
        u'Shell item path: <My Computer> P:\\Application Tools\\Firefox 6.0 '
        u'Index: 8 [MRU Value 2]: Path: Skype.exe, '
        u'Shell item path: <Users Libraries> <UNKNOWN: 0x00>').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
