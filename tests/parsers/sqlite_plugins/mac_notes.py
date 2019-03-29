# -*- coding: utf-8 -*-
"""Tests for mac notes plugin."""
from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_notes as _  # pylint: disable=unused-import
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

    expected_title = 'building 4th brandy gibs'
    self.assertEqual(event.title, expected_title)

    expected_zhtmlstring = (
        '<html><head></head><body style="word-wrap: break-word; '
        '-webkit-nbsp-mode: space; -webkit-line-break: '
        'after-white-space;"><div>building 4th brandy '
        'gibs</div><div><br></div>microsoft office<div>body soul and '
        'peace</div><div>example.com</div><div><br></div><div>3015555555: '
        'plumbing and heating</div><div>claim#123456</div><div><br></div><div'
        '>Small business</div><span class="Apple-tab-span" '
        'style="white-space:pre">	'
        '</span><br><div><br></div><div><br></div></td></tr></tbody></table'
        '></div></td></tr></tbody></table></td></tr></tbody></table></div></td'
        '></tr></tbody></table></td></tr></tbody></table></div></td></tr'
        '></tbody></table></div></body></html>')

    self.assertEqual(event.zhtmlstring, expected_zhtmlstring)

    expected_note_text = (
        '   building 4th brandy gibs\n'
        '      microsoft office\n'
        '   body soul and peace\n'
        '    example.com\n'
        '        3015555555: plumbing and heating\n'
        '    claim#123456\n'
        '        Small business\n            ')
    self.assertEqual(event.note_text, expected_note_text)


    expected_note_body = expected_note_text.replace('\n', '')
    expected_message = 'title: {0:s} note_body: {1:s}'.format(
        expected_title, expected_note_body)

    expected_short_message = 'title: {0:s}'.format(expected_title)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
