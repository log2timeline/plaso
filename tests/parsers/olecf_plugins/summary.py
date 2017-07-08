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
    plugin = summary.SummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'Document.doc'], plugin)

    # There is one summary info stream with three event objects.
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]
    self.assertEqual(event.name, u'Summary Information')

    self.assertEqual(event.title, u'Table of Context')
    self.assertEqual(event.author, u'DAVID NIDES')
    self.assertEqual(event.template, u'Normal.dotm')
    self.assertEqual(event.last_saved_by, u'Nides')
    self.assertEqual(event.revision_number, u'4')
    self.assertEqual(event.number_of_characters, 18)
    self.assertEqual(event.application, u'Microsoft Office Word')
    self.assertEqual(event.security, 0)

    self.assertEqual(event.timestamp_desc, u'Document Creation Time')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-12-10 18:38:00')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
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

    expected_short_message = (
        u'Title: Table of Context '
        u'Author: DAVID NIDES '
        u'Revision number: 4')

    # TODO: add support for:
    #    u'Total edit time (secs): 0 '

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


class TestDocumentSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.doc'])
  def testProcess(self):
    """Tests the Process function on a Document Summary Information stream."""
    plugin = summary.DocumentSummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'Document.doc'], plugin)

    # There should only be one summary info stream with one event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]
    self.assertEqual(event.name, u'Document Summary Information')

    self.assertEqual(event.number_of_lines, 1)
    self.assertEqual(event.number_of_paragraphs, 1)
    self.assertEqual(event.company, u'KPMG')
    self.assertFalse(event.shared_document)
    self.assertEqual(event.application_version, u'14.0')

    # TODO: add support for:
    # self.assertEqual(event.is_shared, False)

    expected_message = (
        u'Number of lines: 1 '
        u'Number of paragraphs: 1 '
        u'Company: KPMG '
        u'Shared document: False '
        u'Application version: 14.0')

    expected_short_message = (
        u'Company: KPMG')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
