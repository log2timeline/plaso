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
    storage_writer = self._ParseDatabaseFileWithPlugin(['NotesV7.storedata'],
                                                       plugin_object)
    
    # TODO: Replace zero with an actual number.
    self.assertEqual(storage_writer.number_of_events, 3)
    self.assertEqual(storage_writer.number_of_errors, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    event = events[0]
    self.CheckTimestamp(event.timestamp, '2014-02-11 02:38:27.097813')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.last_modified_time, '2015-07-31 19:05:46.372972')
    expected_message = ('   building 4th brandy gibs\n'
      '      microsoft office\n'
      '   body soul and peace\n'
      '    example.com\n'
      '        3015555555: plumbing and heating\n'
      '    claim#123456\n'
      '        Small business\n            ')
    self.assertEqual(event.zhtmlstring, expected_message)

if __name__ == '__main__':
  unittest.main()
