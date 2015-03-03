#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File summary and document summary plugins."""

import unittest

from plaso.formatters import olecf as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.olecf_plugins import summary
from plaso.parsers.olecf_plugins import test_lib


class TestSummaryInfoOlecfPlugin(test_lib.OleCfPluginTestCase):
  """Tests for the OLECF summary information plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._summary_plugin = summary.SummaryInfoOlecfPlugin()
    self._test_file = self._GetTestFilePath(['Document.doc'])

  def testProcess(self):
    """Tests the Process function on a SummaryInformation stream."""
    event_queue_consumer = self._ParseOleCfFileWithPlugin(
        self._test_file, self._summary_plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # There is one summary info stream with three event objects.
    self.assertEqual(len(event_objects), 3)

    event_object = event_objects[0]
    self.assertEquals(event_object.name, u'Summary Information')

    self.assertEquals(event_object.title, u'Table of Context')
    self.assertEquals(event_object.author, u'DAVID NIDES')
    self.assertEquals(event_object.template, u'Normal.dotm')
    self.assertEquals(event_object.last_saved_by, u'Nides')
    self.assertEquals(event_object.revision_number, u'4')
    self.assertEquals(event_object.number_of_characters, 18)
    self.assertEquals(event_object.application, u'Microsoft Office Word')
    self.assertEquals(event_object.security, 0)

    self.assertEquals(event_object.timestamp_desc, u'Document Creation Time')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-12-10 18:38:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Title: Table of Context '
        u'Author: DAVID NIDES '
        u'Template: Normal.dotm '
        u'Revision number: 4 '
        u'Last saved by: Nides '
        u'Number of pages: 1 '
        u'Number of words: 3 '
        u'Number of characters: 18 '
        u'Application: Microsoft Office Word '
        u'Security: 0')

    expected_msg_short = (
        u'Title: Table of Context '
        u'Author: DAVID NIDES '
        u'Revision number: 4')

    # TODO: add support for:
    #    u'Total edit time (secs): 0 '

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class TestDocumentSummaryInfoOlecfPlugin(test_lib.OleCfPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._document_summary_plugin = summary.DocumentSummaryOlecfPlugin()
    self._test_file = self._GetTestFilePath(['Document.doc'])

  def testProcess(self):
    """Tests the Process function on a DocumentSummaryInformation stream."""
    event_queue_consumer = self._ParseOleCfFileWithPlugin(
        self._test_file, self._document_summary_plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # There should only be one summary info stream with one event.
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]
    self.assertEqual(event_object.name, u'Document Summary Information')

    self.assertEqual(event_object.number_of_lines, 1)
    self.assertEqual(event_object.number_of_paragraphs, 1)
    self.assertEqual(event_object.company, u'KPMG')
    self.assertFalse(event_object.shared_document)
    self.assertEqual(event_object.application_version, u'14.0')

    # TODO: add support for:
    # self.assertEqual(event_object.is_shared, False)

    expected_msg = (
        u'Number of lines: 1 '
        u'Number of paragraphs: 1 '
        u'Company: KPMG '
        u'Shared document: False '
        u'Application version: 14.0')

    expected_msg_short = (
        u'Company: KPMG')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
