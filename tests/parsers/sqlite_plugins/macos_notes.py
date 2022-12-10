# -*- coding: utf-8 -*-
"""Tests for MacOS notes plugin."""

import unittest

from plaso.parsers.sqlite_plugins import macos_notes

from tests.parsers.sqlite_plugins import test_lib


class MacOSNotesTest(test_lib.SQLitePluginTestCase):
  """Tests for MacOS notes database plugin."""

  def testProcess(self):
    """Test the Process function on a Mac Notes file."""
    plugin_object = macos_notes.MacOSNotesPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['NotesV7.storedata'], plugin_object)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2014-02-11T02:38:27.097813+00:00',
        'data_type': 'macos:notes:entry',
        'modification_time': '2015-07-31T19:05:46.372972+00:00',
        'text': (
            'building 4th brandy gibs microsoft office body soul and peace '
            'example.com 3015555555: plumbing and heating claim#123456 Small '
            'business '),
        'title': 'building 4th brandy gibs'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
