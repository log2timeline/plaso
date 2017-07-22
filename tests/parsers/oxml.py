#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OXML parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import oxml as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import oxml

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class OXMLTest(test_lib.ParserTestCase):
  """Tests for the OXML parser."""

  @shared_test_lib.skipUnlessHasTestFile(['Document.docx'])
  def testParse(self):
    """Tests the Parse function."""
    parser = oxml.OpenXMLParser()
    storage_writer = self._ParseFile(['Document.docx'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString('2012-11-07 23:29:00')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event = events[1]

    self.assertEqual(event.number_of_characters, '13')
    self.assertEqual(event.total_time, '1385')
    self.assertEqual(event.number_of_characters_with_spaces, '14')
    self.assertEqual(event.i4, '1')
    self.assertEqual(event.app_version, '14.0000')
    self.assertEqual(event.number_of_lines, '1')
    self.assertEqual(event.scale_crop, 'false')
    self.assertEqual(event.number_of_pages, '1')
    self.assertEqual(event.number_of_words, '2')
    self.assertEqual(event.links_up_to_date, 'false')
    self.assertEqual(event.number_of_paragraphs, '1')
    self.assertEqual(event.doc_security, '0')
    self.assertEqual(event.hyperlinks_changed, 'false')
    self.assertEqual(event.revision_number, '3')
    self.assertEqual(event.last_saved_by, 'Nides')
    self.assertEqual(event.author, 'Nides')
    self.assertEqual(event.creating_app, 'Microsoft Office Word')
    self.assertEqual(event.template, 'Normal.dotm')

    expected_message = (
        'Creating App: Microsoft Office Word '
        'App version: 14.0000 '
        'Last saved by: Nides '
        'Author: Nides '
        'Revision number: 3 '
        'Template: Normal.dotm '
        'Number of pages: 1 '
        'Number of words: 2 '
        'Number of characters: 13 '
        'Number of characters with spaces: 14 '
        'Number of lines: 1 '
        'Hyperlinks changed: false '
        'Links up to date: false '
        'Scale crop: false')
    expected_short_message = (
        'Author: Nides')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
