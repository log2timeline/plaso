#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Outlook Windows Registry plugins."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import outlook

from tests.parsers.winreg_plugins import test_lib


class MSOutlook2013SearchMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Outlook Search MRU Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Search', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_name = (
        'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
        'username@example.com.ost')
    value_data = b'\xcf\x2b\x37\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        value_name, data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=1892)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = outlook.OutlookSearchMRUPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Outlook\\'
        'Search')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
        'Search')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
        'Search')
    time_string = '2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = outlook.OutlookSearchMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:outlook_search_mru',
        'entries': (
            'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
            'username@example.com.ost: 0x00372bcf'),
        'key_path': key_path,
        'last_written_time': '2012-08-28T09:23:49.0020310+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


# TODO: The catalog for Office 2013 (15.0) contains binary values not
# dword values. Check if Office 2007 and 2010 have the same. Re-enable the
# plug-ins once confirmed and OutlookSearchMRUPlugin has been extended to
# handle the binary data or create a OutlookSearchCatalogMRUPlugin.

# class MSOutlook2013SearchCatalogMRUPluginTest(unittest.TestCase):
#   """Tests for the Outlook Search Catalog MRU Windows Registry plugin."""
#
#   def testProcess(self):
#     """Tests the Process function."""
#     key_path = (
#         'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
#         'Search\\Catalog')
#     time_string = '2012-08-28 09:23:49.002031'
#
#     filetime = dfdatetime_filetime.Filetime()
#     filetime.CopyFromDateTimeString(time_string)
#     registry_key = dfwinreg_fake.FakeWinRegistryKey(
#         'Catalog', key_path=key_path, last_written_time=filetime.timestamp,
#         offset=3421)
#
#     value_name = (
#         'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
#         'username@example.com.ost')
#     value_data = b'\x94\x01\x00\x00\x00\x00'
#     registry_value = dfwinreg_fake.FakeWinRegistryValue(
#         value_name, data=value_data,
#         data_type=dfwinreg_definitions.REG_BINARY, offset=827)
#     registry_key.AddValue(registry_value)
#
#     plugin = outlook.MSOutlook2013SearchCatalogMRUPlugin()
#
#     # TODO: add test for Catalog key.


if __name__ == '__main__':
  unittest.main()
