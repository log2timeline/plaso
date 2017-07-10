#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Outlook Windows Registry plugins."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Search', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_name = (
        u'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
        u'username@example.com.ost')
    value_data = b'\xcf\x2b\x37\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        value_name, data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=1892)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
        u'Search')
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = outlook.OutlookSearchMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
        u'username@example.com.ost: 0x00372bcf').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


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
#         u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
#         u'Search\\Catalog')
#     time_string = u'2012-08-28 09:23:49.002031'
#
#     filetime = dfdatetime_filetime.Filetime()
#     filetime.CopyFromString(time_string)
#     registry_key = dfwinreg_fake.FakeWinRegistryKey(
#         u'Catalog', key_path=key_path, last_written_time=filetime.timestamp,
#         offset=3421)
#
#     value_name = (
#         u'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
#         u'username@example.com.ost')
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
