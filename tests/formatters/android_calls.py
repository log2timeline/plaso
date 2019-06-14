#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android contacts2.db database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_calls

from tests.formatters import test_lib


class AndroidCallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android call history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_calls.AndroidCallFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_calls.AndroidCallFormatter()

    expected_attribute_names = [
        'call_type', 'number', 'name', 'duration']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
