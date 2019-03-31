# -*- coding: utf-8 -*-
"""Tests for mac notes plugin."""
from __future__ import unicode_literals

import unittest
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_notes

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacNotesTest(test_lib.SQLitePluginTestCase):
  """Tests for mac notes database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['NotesV7.storedata'])
  def testProcess(self):
    """Test the Process function on a Mac Notes file."""
    plugin_object = mac_notes.MacNotesPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['NotesV7.storedata'], plugin_object)

    self.assertEqual(storage_writer.number_of_events, 6)
    self.assertEqual(storage_writer.number_of_errors, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    event = events[0]
    self.CheckTimestamp(event.timestamp, '2014-02-11 02:38:27.097813')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.title, 'building 4th brandy gibs')
    expected_message = (
        'note_body:   building 4th brandy gibs'
        '      microsoft office'
        '   body soul and peace'
        '    example.com'
        '        3015555555: plumbing and heating'
        '    claim#123456'
        '        Small business            '
        ' title:building 4th brandy gibs')
    expected_short_message = (
        'title:building 4th brandy gibs')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

if __name__ == '__main__':
  unittest.main()
