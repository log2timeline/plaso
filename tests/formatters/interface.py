#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event formatters interface classes."""

import unittest

from plaso.formatters import interface
from plaso.lib import definitions

from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib


class BooleanEventFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the boolean event formatter helper."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter_helper = interface.BooleanEventFormatterHelper()
    self.assertIsNotNone(event_formatter_helper)

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    event_formatter_helper = interface.BooleanEventFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {}
    event_formatter_helper.FormatEventValues(output_mediator, event_values)


class EnumerationEventFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the enumeration event formatter helper."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter_helper = interface.EnumerationEventFormatterHelper()
    self.assertIsNotNone(event_formatter_helper)

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    event_formatter_helper = interface.EnumerationEventFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {}
    event_formatter_helper.FormatEventValues(output_mediator, event_values)


class FlagsEventFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the flags event formatter helper."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter_helper = interface.FlagsEventFormatterHelper(
        input_attribute='flags', output_attribute='test',
        values={1: 'flag1', 2: 'flag2'})
    self.assertIsNotNone(event_formatter_helper)

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    event_formatter_helper = interface.FlagsEventFormatterHelper(
        input_attribute='flags', output_attribute='test',
        values={1: 'flag1', 2: 'flag2'})

    output_mediator = self._CreateOutputMediator()

    event_values = {'flags': 3}
    event_formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['test'], 'flag1, flag2')

    event_values = {}
    event_formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertNotIn('test', event_values)


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
    event_formatter = interface.BasicEventFormatter(
        data_type='test', format_string='{text}')
    self.assertIsNotNone(event_formatter)

  # TODO: add tests for _FormatMessage
  # TODO: add tests for _FormatMessages

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = interface.BasicEventFormatter(
        data_type='test', format_string='{text}')

    expected_attribute_names = ['text']

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  def testGetMessage(self):
    """Tests the GetMessage function."""
    event_formatter = interface.BasicEventFormatter(
        data_type='test', format_string='{text}')

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    message = event_formatter.GetMessage(event_values)

    self.assertEqual(message, (
         'but we\'re still trying to say something about the event'))

  def testGetMessageShort(self):
    """Tests the GetMessageShort function."""
    event_formatter = interface.BasicEventFormatter(
        data_type='test', format_string='{text}')

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    message_short = event_formatter.GetMessageShort(event_values)

    self.assertEqual(message_short, (
        'but we\'re still trying to say something about the event'))


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

  _TEST_FORMAT_STRING_PIECES = [
      'Description: {description}',
      'Comment',
      'Value: 0x{numeric:02x}',
      'Optional: {optional}',
      'Text: {text}']

  def testCreateFormatStringMaps(self):
    """Tests the _CreateFormatStringMaps function."""
    event_formatter = interface.ConditionalEventFormatter(
        data_type='test', format_string_pieces=self._TEST_FORMAT_STRING_PIECES)
    event_formatter._CreateFormatStringMaps()

    with self.assertRaises(RuntimeError):
      format_string_pieces = ['{too} {many} formatting placeholders']
      event_formatter = interface.ConditionalEventFormatter(
          data_type='test', format_string_pieces=format_string_pieces)
      event_formatter._CreateFormatStringMaps()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = interface.ConditionalEventFormatter(
        data_type='test', format_string_pieces=self._TEST_FORMAT_STRING_PIECES)

    expected_attribute_names = sorted([
        'description', 'numeric', 'optional', 'text'])

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  def testGetMessage(self):
    """Tests the GetMessage function."""
    event_formatter = interface.ConditionalEventFormatter(
        data_type='test', format_string_pieces=self._TEST_FORMAT_STRING_PIECES)

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    message = event_formatter.GetMessage(event_values)

    expected_message = (
        'Description: this is beyond words Comment Value: 0x0c '
        'Text: but we\'re still trying to say something about the event')
    self.assertEqual(message, expected_message)

  def testGetMessageShort(self):
    """Tests the GetMessageShort function."""
    event_formatter = interface.ConditionalEventFormatter(
        data_type='test', format_string_pieces=self._TEST_FORMAT_STRING_PIECES)

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_values = event_data.CopyToDict()

    message_short = event_formatter.GetMessage(event_values)

    expected_message_short = (
        'Description: this is beyond words Comment Value: 0x0c '
        'Text: but we\'re still trying to say something about the event')
    self.assertEqual(message_short, expected_message_short)


if __name__ == '__main__':
  unittest.main()
