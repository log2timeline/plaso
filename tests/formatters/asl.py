#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple System Log (ASL) event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import asl

from tests.formatters import test_lib


class ASLFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Apple System Log (ASL) log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = asl.ASLFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = asl.ASLFormatter()

    expected_attribute_names = [
        'message_id', 'level', 'user_sid', 'group_id', 'read_uid',
        'read_gid', 'computer_name', 'sender', 'facility', 'message',
        'extra_information']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
