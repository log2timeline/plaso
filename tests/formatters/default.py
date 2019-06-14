#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the default event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import default

from tests.formatters import test_lib


class DefaultFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the default event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = default.DefaultFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = default.DefaultFormatter()

    expected_attribute_names = ['attribute_driven']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
