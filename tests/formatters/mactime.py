#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Sleuthkit (TSK) bodyfile (or mactime) event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mactime

from tests.formatters import test_lib


class MactimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the mactime event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mactime.MactimeFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mactime.MactimeFormatter()

    expected_attribute_names = ['filename']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
