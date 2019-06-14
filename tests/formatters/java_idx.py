#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Java WebStart Cache IDX event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import java_idx

from tests.formatters import test_lib


class JavaIDXFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Java WebStart Cache IDX download event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = java_idx.JavaIDXFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = java_idx.JavaIDXFormatter()

    expected_attribute_names = [
        'idx_version',
        'ip_address',
        'url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
