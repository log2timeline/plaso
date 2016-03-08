#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event formatters interface classes."""

import unittest

from plaso.formatters import interface
from plaso.formatters import mediator

from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib


class BrokenConditionalEventFormatter(interface.ConditionalEventFormatter):
  """A broken conditional event formatter."""
  DATA_TYPE = u'test:broken_conditional'
  FORMAT_STRING_PIECES = [u'{too} {many} formatting placeholders']

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Some Text File.'


class ConditionalTestEvent(containers_test_lib.TestEvent):
  DATA_TYPE = u'test:event:conditional'


class ConditionalTestEventFormatter(interface.ConditionalEventFormatter):
  """Class to define a formatter for a conditional test event."""
  DATA_TYPE = u'test:event:conditional'
  FORMAT_STRING_PIECES = [
      u'Description: {description}',
      u'Comment',
      u'Value: 0x{numeric:02x}',
      u'Optional: {optional}',
      u'Text: {text}']

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Some Text File.'


class WrongEventFormatter(interface.EventFormatter):
  """A simple event formatter."""
  DATA_TYPE = u'test:wrong'
  FORMAT_STRING = u'This format string does not match {body}.'

  SOURCE_SHORT = u'FILE'
  SOURCE_LONG = u'Weird Log File'


class EventFormatterTest(unittest.TestCase):
  """Tests for the event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._event_objects = containers_test_lib.GetEventObjects()

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = test_lib.TestEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = test_lib.TestEventFormatter()

    expected_attribute_names = [u'text']

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class ConditionalEventFormatterTest(unittest.TestCase):
  """Tests for the conditional event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._event_object = ConditionalTestEvent(1335791207939596, {
        u'numeric': 12, u'description': u'this is beyond words',
        u'text': u'but we\'re still trying to say something about the event'})

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ConditionalTestEventFormatter()
    self.assertIsNotNone(event_formatter)

    with self.assertRaises(RuntimeError):
      _ = BrokenConditionalEventFormatter()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ConditionalTestEventFormatter()

    expected_attribute_names = sorted([
        u'description', u'numeric', u'optional', u'text'])

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages function."""
    formatter_mediator = mediator.FormatterMediator()
    event_formatter = ConditionalTestEventFormatter()

    expected_message = (
        u'Description: this is beyond words Comment Value: 0x0c '
        u'Text: but we\'re still trying to say something about the event')

    message, _ = event_formatter.GetMessages(
        formatter_mediator, self._event_object)
    self.assertEqual(message, expected_message)

  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
