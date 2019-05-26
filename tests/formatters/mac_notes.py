
# !/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Mac Notes event formatter."""
from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_notes
from tests.formatters import test_lib


class MacNotesZhtmlstringFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Mac Notes zhtmlstring event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_notes.MacNotesNotesFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_notes.MacNotesNotesFormatter()

    expected_attribute_names = ['text', 'title']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
