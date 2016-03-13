#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OXML parser."""

import unittest

from plaso.formatters import oxml as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import oxml

from tests.parsers import test_lib


class OXMLTest(test_lib.ParserTestCase):
  """Tests for the OXML parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = oxml.OpenXMLParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'Document.docx'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-07 23:29:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    event_object = event_objects[1]

    self.assertEqual(event_object.number_of_characters, u'13')
    self.assertEqual(event_object.total_time, u'1385')
    self.assertEqual(event_object.number_of_characters_with_spaces, u'14')
    self.assertEqual(event_object.i4, u'1')
    self.assertEqual(event_object.app_version, u'14.0000')
    self.assertEqual(event_object.number_of_lines, u'1')
    self.assertEqual(event_object.scale_crop, u'false')
    self.assertEqual(event_object.number_of_pages, u'1')
    self.assertEqual(event_object.number_of_words, u'2')
    self.assertEqual(event_object.links_up_to_date, u'false')
    self.assertEqual(event_object.number_of_paragraphs, u'1')
    self.assertEqual(event_object.doc_security, u'0')
    self.assertEqual(event_object.hyperlinks_changed, u'false')
    self.assertEqual(event_object.revision_number, u'3')
    self.assertEqual(event_object.last_saved_by, u'Nides')
    self.assertEqual(event_object.author, u'Nides')
    self.assertEqual(
        event_object.creating_app, u'Microsoft Office Word')
    self.assertEqual(event_object.template, u'Normal.dotm')

    expected_msg = (
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
    expected_msg_short = (
        u'Author: Nides')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
