#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SCCM log event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import sccm
from tests.formatters import test_lib


class SCCMFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SCCM log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = sccm.SCCMEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = sccm.SCCMEventFormatter()

    expected_attribute_names = [
        'text',
        'component']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
