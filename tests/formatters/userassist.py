#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry event formatter."""

from __future__ import unicode_literals

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
        'key_path',
        'entry_index',
        'value_name',
        'number_of_executions',
        'application_focus_count',
        'application_focus_duration']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
