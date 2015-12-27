#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler event formatter."""

import unittest

from plaso.formatters import task_scheduler

from tests.formatters import test_lib


class TaskCacheEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Task Scheduler Cache event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = task_scheduler.TaskCacheEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = task_scheduler.TaskCacheEventFormatter()

    expected_attribute_names = [
        u'task_name',
        u'task_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
