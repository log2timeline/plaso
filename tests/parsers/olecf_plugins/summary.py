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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # TODO: add support for: 'Total edit time (secs): 0'

    expected_event_values = {
        'application': 'Microsoft Office Word',
        'author': 'DAVID NIDES',
        'data_type': 'olecf:summary_info',
        'date_time': '2012-12-10 18:38:00.0000000',
        'last_saved_by': 'Nides',
        'name': 'Summary Information',
        'number_of_characters': 18,
        'number_of_pages': 1,
        'number_of_words': 3,
        'revision_number': '4',
        'security': 0,
        'template': 'Normal.dotm',
        'timestamp_desc': 'Document Creation Time',
        'title': 'Table of Context'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


class TestDocumentSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  def testProcess(self):
    """Tests the Process function on a Document Summary Information stream."""
    plugin = summary.DocumentSummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'application_version': '14.0',
        'company': 'KPMG',
        'data_type': 'olecf:document_summary_info',
        'date_time': '2013-05-16 02:29:49.7950000',
        'name': 'Document Summary Information',
        'number_of_lines': 1,
        'number_of_paragraphs': 1,
        'shared_document': False}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
