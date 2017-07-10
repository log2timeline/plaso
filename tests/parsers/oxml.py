#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OXML parser."""

import unittest

from plaso.formatters import oxml  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import oxml

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class OXMLTest(test_lib.ParserTestCase):
  """Tests for the OXML parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.docx'])
  def testParse(self):
    """Tests the Parse function."""
    parser = oxml.OpenXMLParser()
    storage_writer = self._ParseFile([u'Document.docx'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-07 23:29:00')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event = events[1]

    self.assertEqual(event.number_of_characters, u'13')
    self.assertEqual(event.total_time, u'1385')
    self.assertEqual(event.number_of_characters_with_spaces, u'14')
    self.assertEqual(event.i4, u'1')
    self.assertEqual(event.app_version, u'14.0000')
    self.assertEqual(event.number_of_lines, u'1')
    self.assertEqual(event.scale_crop, u'false')
    self.assertEqual(event.number_of_pages, u'1')
    self.assertEqual(event.number_of_words, u'2')
    self.assertEqual(event.links_up_to_date, u'false')
    self.assertEqual(event.number_of_paragraphs, u'1')
    self.assertEqual(event.doc_security, u'0')
    self.assertEqual(event.hyperlinks_changed, u'false')
    self.assertEqual(event.revision_number, u'3')
    self.assertEqual(event.last_saved_by, u'Nides')
    self.assertEqual(event.author, u'Nides')
    self.assertEqual(
        event.creating_app, u'Microsoft Office Word')
    self.assertEqual(event.template, u'Normal.dotm')

    expected_message = (
        u'Creating App: Microsoft Office Word '
        u'App version: 14.0000 '
        u'Last saved by: Nides '
        u'Author: Nides '
        u'Revision number: 3 '
        u'Template: Normal.dotm '
        u'Number of pages: 1 '
        u'Number of words: 2 '
        u'Number of characters: 13 '
        u'Number of characters with spaces: 14 '
        u'Number of lines: 1 '
        u'Hyperlinks changed: false '
        u'Links up to date: false '
        u'Scale crop: false')
    expected_short_message = (
        u'Author: Nides')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
