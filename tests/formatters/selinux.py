#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the selinux event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import selinux

from tests.formatters import test_lib


class SELinuxFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the selinux log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = selinux.SELinuxFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = selinux.SELinuxFormatter()

    expected_attribute_names = [
        'audit_type',
        'pid',
        'body']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
