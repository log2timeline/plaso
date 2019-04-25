#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import olecf

from tests.formatters import test_lib


class OLECFItemFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the OLECF item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = olecf.OLECFItemFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = olecf.OLECFItemFormatter()

    expected_attribute_names = ['name']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class OLECFDestListEntryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the DestList stream event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = olecf.OLECFDestListEntryFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = olecf.OLECFDestListEntryFormatter()

    expected_attribute_names = [
        'entry_number',
        'pin_status',
        'hostname',
        'path',
        'droid_volume_identifier',
        'droid_file_identifier',
        'birth_droid_volume_identifier',
        'birth_droid_file_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class OLECFDocumentSummaryInfoFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Document Summary Info property set stream event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = olecf.OLECFDocumentSummaryInfoFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = olecf.OLECFDocumentSummaryInfoFormatter()

    expected_attribute_names = [
        'number_of_bytes',
        'number_of_lines',
        'number_of_paragraphs',
        'number_of_slides',
        'number_of_notes',
        'number_of_hidden_slides',
        'number_of_clips',
        'company',
        'manager',
        'shared_document',
        'application_version',
        'content_type',
        'content_status',
        'language',
        'document_version']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class OLECFSummaryInfoFormatter(test_lib.EventFormatterTestCase):
  """Tests for the Summary Info property set stream event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = olecf.OLECFSummaryInfoFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = olecf.OLECFSummaryInfoFormatter()

    expected_attribute_names = [
        'title',
        'subject',
        'author',
        'keywords',
        'comments',
        'template',
        'revision_number',
        'last_saved_by',
        'total_edit_time',
        'number_of_pages',
        'number_of_words',
        'number_of_characters',
        'application',
        'security']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
