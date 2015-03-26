#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Hachoir event formatter."""

import unittest

from plaso.formatters import hachoir
from plaso.formatters import test_lib


class HachoirFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Hachoir event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = hachoir.HachoirFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = hachoir.HachoirFormatter()

    expected_attribute_names = [u'data']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
