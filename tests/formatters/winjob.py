#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Scheduled Task (job) event formatter."""

import unittest

from plaso.formatters import winjob

from tests.formatters import test_lib


class WinJobFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Scheduled Task (job) event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winjob.WinJobFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winjob.WinJobFormatter()

    expected_attribute_names = [
        u'application',
        u'parameters',
        u'trigger_type',
        u'username',
        u'working_directory']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
