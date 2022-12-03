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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application': 'Microsoft Office Word',
        'author': 'DAVID NIDES',
        'creation_time': '2012-12-10T18:38:00.0000000+00:00',
        'data_type': 'olecf:summary_info',
        'edit_duration': None,
        'item_creation_time': None,
        'item_modification_time': '2013-05-16T02:29:49.7950000+00:00',
        'last_printed_time': None,
        'last_save_time': '2013-05-16T02:29:00.0000000+00:00',
        'last_saved_by': 'Nides',
        'number_of_characters': 18,
        'number_of_pages': 1,
        'number_of_words': 3,
        'revision_number': '4',
        'security_flags': 0,
        'template': 'Normal.dotm',
        'title': 'Table of Context'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TestDocumentSummaryInformationOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF document summary information plugin."""

  def testProcess(self):
    """Tests the Process function on a Document Summary Information stream."""
    plugin = summary.DocumentSummaryInformationOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application_version': '14.0',
        'company': 'KPMG',
        'data_type': 'olecf:document_summary_info',
        'item_creation_time': None,
        'item_modification_time': '2013-05-16T02:29:49.7950000+00:00',
        'links_up_to_date': False,
        'number_of_lines': 1,
        'number_of_paragraphs': 1,
        'shared_document': False}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
