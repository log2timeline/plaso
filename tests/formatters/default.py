#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the default event formatter."""

import unittest

from plaso.formatters import default
from plaso.lib import definitions

from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib


class DefaultEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the default event formatter."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'description': 'this is beyond words',
       'numeric': 12,
       'text': 'but we\'re still trying to say something about the event',
       'timestamp': 1335791207939596,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = default.DefaultEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = default.DefaultEventFormatter()

    expected_attribute_names = ['attribute_values']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  def testGetMessage(self):
    """Tests the GetMessage function."""
    event_formatter = default.DefaultEventFormatter()

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    expected_message = (
        '<WARNING DEFAULT FORMATTER> Attributes: '
        'description: this is beyond words '
        'numeric: 12 '
        'text: but we\'re still trying to say something about the event')

    message = event_formatter.GetMessage(event_values)
    self.assertEqual(message, expected_message)

  def testGetMessageShort(self):
    """Tests the GetMessageShort function."""
    event_formatter = default.DefaultEventFormatter()

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    expected_message_short = (
        '<DEFAULT> '
        'description: this is beyond words '
        'numeric: 12 '
        'text: but we\'re still...')

    message_short = event_formatter.GetMessageShort(event_values)
    self.assertEqual(message_short, expected_message_short)


if __name__ == '__main__':
  unittest.main()
