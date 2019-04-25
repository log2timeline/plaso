#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS launch services (LS) quarantine event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ls_quarantine

from tests.formatters import test_lib


class LSQuarantineFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the launch services (LS) quarantine history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ls_quarantine.LSQuarantineFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ls_quarantine.LSQuarantineFormatter()

    expected_attribute_names = [
        'agent',
        'url',
        'data']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
