#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File summary and document summary plugins."""

import unittest

from plaso.parsers.olecf_plugins import summary

from tests.parsers.olecf_plugins import test_lib


class TestSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF summary information plugin."""

  def testProcess(self):
    """Tests the Process function on a Summary Information stream."""
    plugin = summary.SummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'application': 'Microsoft Office Word',
        'author': 'DAVID NIDES',
        'last_saved_by': 'Nides',
        'name': 'Summary Information',
        'number_of_characters': 18,
        'revision_number': '4',
        'security': 0,
        'template': 'Normal.dotm',
        'timestamp': '2012-12-10 18:38:00.000000',
        'timestamp_desc': 'Document Creation Time',
        'title': 'Table of Context'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Title: Table of Context '
        'Author: DAVID NIDES '
        'Template: Normal.dotm '
        'Revision number: 4 '
        'Last saved by: Nides '
        'Number of pages: 1 '
        'Number of words: 3 '
        'Number of characters: 18 '
        'Application: Microsoft Office Word '
        'Security flags: 0x00000000')

    expected_short_message = (
        'Title: Table of Context '
        'Author: DAVID NIDES '
        'Revision number: 4')

    # TODO: add support for:
    #    'Total edit time (secs): 0 '

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


class TestDocumentSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  def testProcess(self):
    """Tests the Process function on a Document Summary Information stream."""
    plugin = summary.DocumentSummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'application_version': '14.0',
        'company': 'KPMG',
        'name': 'Document Summary Information',
        'number_of_lines': 1,
        'number_of_paragraphs': 1,
        'shared_document': False}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # TODO: add support for:
    # self.assertFalse(event_data.is_shared)

    expected_message = (
        'Number of lines: 1 '
        'Number of paragraphs: 1 '
        'Company: KPMG '
        'Shared document: False '
        'Application version: 14.0')

    expected_short_message = (
        'Company: KPMG')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
