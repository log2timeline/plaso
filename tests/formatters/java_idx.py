#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Java WebStart Cache IDX event formatter."""

import unittest

from plaso.formatters import java_idx

from tests.formatters import test_lib


class JavaIDXFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Java WebStart Cache IDX download event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = java_idx.JavaIDXFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = java_idx.JavaIDXFormatter()

    expected_attribute_names = [
        u'idx_version',
        u'ip_address',
        u'url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
