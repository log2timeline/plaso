# -*- coding: utf-8 -*-
"""Tests for the iOS Notes database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_notes

from tests.parsers.sqlite_plugins import test_lib


class IOSNotesTest(test_lib.SQLitePluginTestCase):
  """Tests for the iOS Notes database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_notes.IOSNotesPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['NotesStore.sqlite'], plugin)
    
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 28)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2023-05-10T00:56:26.719389',
        'modification_time': '2023-05-10T00:57:01.178374',
        'title': 'iOS 15 Note',
        'snippet': 'Here is the test iOS 15 note.'}
    
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 25)
    self.CheckEventData(event_data, expected_event_values)
  

  if __name__ == '__main__':
    unittest.main()
