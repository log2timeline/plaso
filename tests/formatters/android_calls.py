#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android contacts2.db database event formatter."""

import unittest

from plaso.formatters import android_calls

from tests.formatters import test_lib


class AndroidCallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android call history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_calls.AndroidCallFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_calls.AndroidCallFormatter()

    expected_attribute_names = [
        u'call_type', u'number', u'name', u'duration']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
