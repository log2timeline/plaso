#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OpenXML event formatter."""

import unittest

from plaso.formatters import oxml

from tests.formatters import test_lib


class OpenXMLParserFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the OXML event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = oxml.OpenXMLParserFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = oxml.OpenXMLParserFormatter()

    expected_attribute_names = [
        u'creating_app',
        u'app_version',
        u'title',
        u'subject',
        u'last_saved_by',
        u'author',
        u'total_edit_time',
        u'keywords',
        u'comments',
        u'revision_number',
        u'template',
        u'number_of_pages',
        u'number_of_words',
        u'number_of_characters',
        u'number_of_characters_with_spaces',
        u'number_of_lines',
        u'company',
        u'manager',
        u'shared',
        u'security',
        u'hyperlinks_changed',
        u'links_up_to_date',
        u'scale_crop',
        u'dig_sig',
        u'slides',
        u'hidden_slides',
        u'presentation_format',
        u'mm_clips',
        u'notes']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
