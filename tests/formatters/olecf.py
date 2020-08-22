#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import olecf

from tests.formatters import test_lib


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
