#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Basic Security Module (BSM) binary files event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import bsm

from tests.formatters import test_lib


class BSMFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the BSM log entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = bsm.BSMFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = bsm.BSMFormatter()

    expected_attribute_names = [
        'event_type',
        'event_type_string',
        'return_value',
        'extra_tokens']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
