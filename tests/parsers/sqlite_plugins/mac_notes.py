# -*- coding: utf-8 -*-
"""Tests for mac notes plugin."""
import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_notes

from tests.parsers.sqlite_plugins import test_lib


class MacNotesTest(test_lib.SQLitePluginTestCase):
  """Tests for mac notes database plugin."""

  def testProcess(self):
    """Test the Process function on a Mac Notes file."""
    plugin_object = mac_notes.MacNotesPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['NotesV7.storedata'], plugin_object)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:notes:note',
        'date_time': '2014-02-11 02:38:27.097813',
        'text': (
            'building 4th brandy gibs microsoft office body soul and peace '
            'example.com 3015555555: plumbing and heating claim#123456 Small '
            'business '),
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'building 4th brandy gibs'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
