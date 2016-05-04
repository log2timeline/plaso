#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog cron event formatter."""

import unittest

from plaso.formatters import cron

from tests.formatters import test_lib


class CronEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the syslog cron task run event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = cron.CronTaskRunEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = cron.CronTaskRunEventFormatter()

    expected_attribute_names = [
        u'command', u'username', u'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.

if __name__ == '__main__':
  unittest.main()
