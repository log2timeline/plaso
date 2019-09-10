#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry BAM entries event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import bam

from tests.formatters import test_lib


class BackgroundActivityModeratorFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the BAM Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = bam.BackgroundActivityModeratorFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = bam.BackgroundActivityModeratorFormatter()

    expected_attribute_names = ['binary_path', 'user_sid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
