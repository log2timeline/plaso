#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) event formatters."""

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

    expected_attribute_names = [u'name']

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
        u'entry_number',
        u'pin_status',
        u'hostname',
        u'path',
        u'droid_volume_identifier',
        u'droid_file_identifier',
        u'birth_droid_volume_identifier',
        u'birth_droid_file_identifier']

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
        u'number_of_bytes',
        u'number_of_lines',
        u'number_of_paragraphs',
        u'number_of_slides',
        u'number_of_notes',
        u'number_of_hidden_slides',
        u'number_of_clips',
        u'company',
        u'manager',
        u'shared_document',
        u'application_version',
        u'content_type',
        u'content_status',
        u'language',
        u'document_version']

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
        u'title',
        u'subject',
        u'author',
        u'keywords',
        u'comments',
        u'template',
        u'revision_number',
        u'last_saved_by',
        u'total_edit_time',
        u'number_of_pages',
        u'number_of_words',
        u'number_of_characters',
        u'application',
        u'security']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
