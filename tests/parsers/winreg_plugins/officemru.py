#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

import unittest

from plaso.formatters import officemru  # pylint: disable=unused-import
from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import officemru

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Microsoft Office MRUs Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER-WIN7.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Word\\'
        u'File MRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = officemru.OfficeMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 6)

    event_object = storage_writer.events[5]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-13 18:27:15.089802')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    regvalue_identifier = u'Item 1'
    expected_value_string = (
        u'[F00000000][T01CD0146EA1EADB0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        u'SA-23E Mitchell-Hyundyne Starfury.docx')
    self._TestRegvalue(event_object, regvalue_identifier, expected_value_string)

    expected_message = (
        u'[{0:s}] '
        u'{1:s}: {2:s} '
        u'Item 2: [F00000000][T01CD00921FC127F0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\Earthforce SA-26 '
        u'Thunderbolt Star Fury.docx '
        u'Item 3: [F00000000][T01CD009208780140][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\StarFury.docx '
        u'Item 4: [F00000000][T01CCFE0B22DA9EF0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\VIBRANIUM.docx '
        u'Item 5: [F00000000][T01CCFCBA595DFC30][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\ADAMANTIUM-Background.docx').format(
            key_path, regvalue_identifier, expected_value_string)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # Test OfficeMRUWindowsRegistryEvent.
    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-13 18:27:15.083')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    self.assertEqual(event_object.value_string, expected_value_string)

    expected_message = u'[{0:s}] Value: {1:s}'.format(
        key_path, expected_value_string)
    expected_short_message = u'{0:s}...'.format(expected_value_string[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
