#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Tango on Android databases event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import tango_android
from tests.formatters import test_lib


class TangoAndroidMessageFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Tango on Android message event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = tango_android.TangoAndroidMessageFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = tango_android.TangoAndroidMessageFormatter()

    expected_attribute_names = [
        'direction',
        'message_identifier',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TangoAndroidConversationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Tango on Android conversation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = tango_android.TangoAndroidConversationFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = tango_android.TangoAndroidConversationFormatter()

    expected_attribute_names = [
        'conversation_identifier'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TangoAndroidContactFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Tango on Android contact event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = tango_android.TangoAndroidContactFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = tango_android.TangoAndroidContactFormatter()

    expected_attribute_names = [
        'first_name',
        'last_name',
        'gender',
        'birthday',
        'status',
        'is_friend',
        'friend_request_type',
        'friend_request_message'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
