#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Advanced Packaging Tool (APT) History log event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import apt_history

from tests.formatters import test_lib


class AptHistoryLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the APT History log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = apt_history.APTHistoryLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = apt_history.APTHistoryLogFormatter()

    expected_attribute_names = [
        'packages',
        'command',
        'error',
        'requester']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
