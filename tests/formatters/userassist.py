#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry event formatter."""

import unittest

from plaso.formatters import userassist

from tests.formatters import test_lib


class UserAssistWindowsRegistryEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the UserAssist Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = userassist.UserAssistWindowsRegistryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = userassist.UserAssistWindowsRegistryEventFormatter()

    expected_attribute_names = [
        u'key_path',
        u'entry_index',
        u'value_name',
        u'number_of_executions',
        u'application_focus_count',
        u'application_focus_duration']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
