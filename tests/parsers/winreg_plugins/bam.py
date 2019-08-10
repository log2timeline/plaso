#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the BAM Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfvfs.path import fake_path_spec
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import bam

from tests.parsers.winreg_plugins import test_lib


class TestFileEntry(object):
  """File entry object for testing purposes.

  Attributes:
    name (str): name of the file entry.
    path_spec (dfvfs.PathSpec): path specification of the file entry.
  """

  def __init__(self, name):
    """Initializes a file entry.

    Args:
      name (str): the file entry name.
    """
    super(TestFileEntry, self).__init__()
    self.name = name
    self.path_spec = fake_path_spec.FakePathSpec(location=name)

  # pylint: disable=redundant-returns-doc
  def GetStat(self):
    """Retrieves the stat object.

    Returns:
      dfvfs.VFSStat: None for testing.
    """
    return None


class BackgroundActivityModeratorWindowsRegistryPluginTest(
    test_lib.RegistryPluginTestCase):
  """Tests for the BAM Windows Registry plugin."""

  _TEST_DATA = bytes(bytearray([
      0x15, 0x3e, 0xae, 0x36, 0x57, 0xde, 0xd4, 0x01,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]))

  def _CreateTestKey(self, binary_data):
    """Creates Registry keys and values for testing.

    Args:
      binary_data (bytes): BAM Registry value data.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    key_path = '\\ControlSet001\\Services\\bam\\State'
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString('2019-03-19 20:55:19.975237')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'UserSettings',
        key_path=key_path,
        last_written_time=filetime.timestamp)

    filetime.CopyFromDateTimeString('2019-03-19 13:29:56.008214')

    sid_key = dfwinreg_fake.FakeWinRegistryKey(
        'S-1-5-21-321011808-3761883066-353627080-1000',
        last_written_time=filetime.timestamp)

    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        (
            '\\Device\\HarddiskVolume1\\Windows\\System32\\WindowsPowerShell'
            '\\v1.0\\powershell.exe'),
        data=binary_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    sid_key.AddValue(registry_value)

    registry_key.AddSubkey(sid_key)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = bam.BackgroundActivityModeratorWindowsRegistryPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
        '\\UserSettings')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
        '\\State\\UserSettings')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessValue(self):
    """Tests the Process function for BAM data."""
    test_file_entry = TestFileEntry('SYSTEM')
    registry_key = self._CreateTestKey(self._TEST_DATA)
    plugin = bam.BackgroundActivityModeratorWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry,
        parser_chain=plugin.plugin_name)

    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event_index = 0
    event = events[event_index]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '\\Device\\HarddiskVolume1\\Windows\\System32\\WindowsPowerShell\\'
        'v1.0\\powershell.exe [S-1-5-21-321011808-3761883066-353627080-1000]')

    expected_short_message = (
        '\\Device\\HarddiskVolume1\\Windows\\System32\\WindowsPowerShell\\v1.0'
        '\\powershell.exe')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
