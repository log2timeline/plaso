#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OpenXML event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import oxml

from tests.formatters import test_lib


class OpenXMLParserFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the OXML event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = oxml.OpenXMLParserFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = oxml.OpenXMLParserFormatter()

    expected_attribute_names = [
        'creating_app',
        'app_version',
        'title',
        'subject',
        'last_saved_by',
        'author',
        'total_edit_time',
        'keywords',
        'comments',
        'revision_number',
        'template',
        'number_of_pages',
        'number_of_words',
        'number_of_characters',
        'number_of_characters_with_spaces',
        'number_of_lines',
        'company',
        'manager',
        'shared',
        'security',
        'hyperlinks_changed',
        'links_up_to_date',
        'scale_crop',
        'dig_sig',
        'slides',
        'hidden_slides',
        'presentation_format',
        'mm_clips',
        'notes']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
