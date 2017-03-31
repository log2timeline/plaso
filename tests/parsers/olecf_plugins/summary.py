#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File summary and document summary plugins."""

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.olecf_plugins import summary

from tests import test_lib as shared_test_lib
from tests.parsers.olecf_plugins import test_lib


class TestSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF summary information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.doc'])
  def testProcess(self):
    """Tests the Process function on a Summary Information stream."""
    plugin_object = summary.SummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'Document.doc'], plugin_object)

    # There is one summary info stream with three event objects.
    self.assertEqual(len(storage_writer.events), 3)

    events = self._GetSortedEvents(storage_writer.events)

    event_object = events[0]
    self.assertEqual(event_object.name, u'Summary Information')

    self.assertEqual(event_object.title, u'Table of Context')
    self.assertEqual(event_object.author, u'DAVID NIDES')
    self.assertEqual(event_object.template, u'Normal.dotm')
    self.assertEqual(event_object.last_saved_by, u'Nides')
    self.assertEqual(event_object.revision_number, u'4')
    self.assertEqual(event_object.number_of_characters, 18)
    self.assertEqual(event_object.application, u'Microsoft Office Word')
    self.assertEqual(event_object.security, 0)

    self.assertEqual(event_object.timestamp_desc, u'Document Creation Time')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-12-10 18:38:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

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


class TestDocumentSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.doc'])
  def testProcess(self):
    """Tests the Process function on a Document Summary Information stream."""
    plugin_object = summary.DocumentSummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'Document.doc'], plugin_object)

    # There should only be one summary info stream with one event.
    self.assertEqual(len(storage_writer.events), 1)

    events = self._GetSortedEvents(storage_writer.events)

    event_object = events[0]
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
