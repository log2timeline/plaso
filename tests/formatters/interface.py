#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event formatters interface classes."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import interface
from plaso.formatters import mediator
from plaso.lib import definitions

from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib


class BrokenConditionalEventFormatter(interface.ConditionalEventFormatter):
  """An event object for testing the conditional event formatter."""
  DATA_TYPE = 'test:broken_conditional'
  FORMAT_STRING_PIECES = ['{too} {many} formatting placeholders']

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Some Text File.'


class ConditionalTestEventFormatter(interface.ConditionalEventFormatter):
  """A test conditional event formatter."""

  DATA_TYPE = 'test:event:conditional'

  FORMAT_STRING_PIECES = [
      'Description: {description}',
      'Comment',
      'Value: 0x{numeric:02x}',
      'Optional: {optional}',
      'Text: {text}']

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Some Text File.'


class WrongEventFormatter(interface.EventFormatter):
  """An event formatter for testing."""
  DATA_TYPE = 'test:wrong'

  FORMAT_STRING = 'This format string does not match {body}.'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class EventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the event formatter."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'description': 'this is beyond words',
       'numeric': 12,
       'text': 'but we\'re still trying to say something about the event',
       'timestamp': 1335791207939596,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = test_lib.TestEventFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add tests for _FormatMessage
  # TODO: add tests for _FormatMessages

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = test_lib.TestEventFormatter()

    expected_attribute_names = ['text']

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages function."""
    formatter_mediator = mediator.FormatterMediator()
    event_formatter = test_lib.TestEventFormatter()

    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    message, _ = event_formatter.GetMessages(formatter_mediator, event_data)

    self.assertEqual(
        message, 'but we\'re still trying to say something about the event')

  # TODO: add tests for GetSources


class ConditionalEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the conditional event formatter."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event:conditional',
       'description': 'this is beyond words',
       'numeric': 12,
       'text': 'but we\'re still trying to say something about the event',
       'timestamp': 1335791207939596,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testCreateFormatStringMaps(self):
    """Tests the _CreateFormatStringMaps function."""
    event_formatter = ConditionalTestEventFormatter()
    event_formatter._CreateFormatStringMaps()

    with self.assertRaises(RuntimeError):
      event_formatter = BrokenConditionalEventFormatter()
      event_formatter._CreateFormatStringMaps()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ConditionalTestEventFormatter()

    expected_attribute_names = sorted([
        'description', 'numeric', 'optional', 'text'])

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages function."""
    formatter_mediator = mediator.FormatterMediator()
    event_formatter = ConditionalTestEventFormatter()

    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    message, _ = event_formatter.GetMessages(formatter_mediator, event_data)

    expected_message = (
        'Description: this is beyond words Comment Value: 0x0c '
        'Text: but we\'re still trying to say something about the event')
    self.assertEqual(message, expected_message)

  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
