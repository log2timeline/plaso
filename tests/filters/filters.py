#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser filter classes."""

import unittest

from plaso.containers import events
from plaso.filters import filters
from plaso.lib import definitions

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib


class FalseFilter(filters.Operator):
  """A filter which always evaluates to False for testing."""

  def Matches(self, event, event_data, event_data_stream, event_tag):
    """Determines if the event, data and tag match the filter.

    Args:
      event (EventObject): event to compare against the filter.
      event_data (EventData): event data to compare against the filter.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag to compare against the filter.

    Returns:
      bool: True if the event, data and tag match the filter, False otherwise.
    """
    return False


class TrueFilter(filters.Operator):
  """A filter which always evaluates to True for testing."""

  def Matches(self, event, event_data, event_data_stream, event_tag):
    """Determines if the event, data and tag match the filter.

    Args:
      event (EventObject): event to compare against the filter.
      event_data (EventData): event data to compare against the filter.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag to compare against the filter.

    Returns:
      bool: True if the event, data and tag match the filter, False otherwise.
    """
    return True


class FilterTest(shared_test_lib.BaseTestCase):
  """Tests the filter."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    filter_object = filters.Filter()
    self.assertIsNotNone(filter_object)

  def testCopyValueToString(self):
    """Tests the _CopyValueToString function."""
    filter_object = filters.Filter()

    string = filter_object._CopyValueToString(['1', '2', '3'])
    self.assertEqual(string, '123')

    string = filter_object._CopyValueToString([1, 2, 3])
    self.assertEqual(string, '123')

    string = filter_object._CopyValueToString(123)
    self.assertEqual(string, '123')

    string = filter_object._CopyValueToString(b'123')
    self.assertEqual(string, '123')

    string = filter_object._CopyValueToString('123')
    self.assertEqual(string, '123')


class AndFilterTest(shared_test_lib.BaseTestCase):
  """Tests the boolean AND filter."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'test_value': 1,
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testMatches(self):
    """Tests the Matches function."""
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    false_filter_object = FalseFilter()
    true_filter_object = TrueFilter()

    filter_object = filters.AndFilter(arguments=[
        true_filter_object, true_filter_object])

    result = filter_object.Matches(event, event_data, None, None)
    self.assertTrue(result)

    filter_object = filters.AndFilter(arguments=[
        false_filter_object, true_filter_object])

    result = filter_object.Matches(event, event_data, None, None)
    self.assertFalse(result)


class OrFilterTest(shared_test_lib.BaseTestCase):
  """Tests the boolean OR filter."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'test_value': 1,
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testMatches(self):
    """Tests the Matches function."""
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    false_filter_object = FalseFilter()
    true_filter_object = TrueFilter()

    filter_object = filters.OrFilter(arguments=[
        false_filter_object, true_filter_object])

    result = filter_object.Matches(event, event_data, None, None)
    self.assertTrue(result)

    filter_object = filters.OrFilter(arguments=[
        false_filter_object, false_filter_object])

    result = filter_object.Matches(event, event_data, None, None)
    self.assertFalse(result)


class IdentityFilterTest(shared_test_lib.BaseTestCase):
  """Tests the filter which always evaluates to True."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'test_value': 1,
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testMatches(self):
    """Tests the Matches function."""
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    filter_object = filters.IdentityFilter()

    result = filter_object.Matches(event, event_data, None, None)
    self.assertTrue(result)


class BinaryOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the binary operators interface."""

  def testInitialize(self):
    """Tests the __init__ function."""
    filter_object = filters.BinaryOperator(arguments=['test_value', 1])
    self.assertIsNotNone(filter_object)


class GenericBinaryOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the shared functionality for common binary operators."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'test_value': 1,
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testInitialize(self):
    """Tests the __init__ function."""
    filter_object = filters.GenericBinaryOperator(arguments=['test_value', 1])
    self.assertIsNotNone(filter_object)

  def testGetValue(self):
    """Tests the _GetValue function."""
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    event_tag = events.EventTag()
    event_tag.AddLabel('browser_search')

    filter_object = filters.GenericBinaryOperator(arguments=['test_value', 1])

    test_value = filter_object._GetValue(
        'test_value', event, event_data, None, event_tag)
    self.assertEqual(test_value, 1)

    test_value = filter_object._GetValue(
        'timestamp', event, event_data, None, event_tag)
    self.assertIsNotNone(test_value)
    self.assertEqual(test_value.timestamp, 5134324321)

    test_value = filter_object._GetValue(
        'tag', event, event_data, None, event_tag)
    self.assertEqual(test_value, ['browser_search'])

  # TODO: add tests for FlipBool function


class EqualsOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the equals operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.EqualsOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertFalse(result)

    result = filter_object._CompareValue(10, 10)
    self.assertTrue(result)


class NotEqualsOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the not equals operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.NotEqualsOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertTrue(result)

    result = filter_object._CompareValue(10, 10)
    self.assertFalse(result)


class LessThanOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the less than operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.LessThanOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertTrue(result)

    result = filter_object._CompareValue(10, 10)
    self.assertFalse(result)

    result = filter_object._CompareValue(20, 10)
    self.assertFalse(result)


class LessEqualOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the less equal operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.LessEqualOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertTrue(result)

    result = filter_object._CompareValue(10, 10)
    self.assertTrue(result)

    result = filter_object._CompareValue(20, 10)
    self.assertFalse(result)


class GreaterThanOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the greater than operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.GreaterThanOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertFalse(result)

    result = filter_object._CompareValue(10, 10)
    self.assertFalse(result)

    result = filter_object._CompareValue(20, 10)
    self.assertTrue(result)


class GreaterEqualOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the greater equal operator."""

  # pylint: disable=protected-access

  def testCompareValue(self):
    """Tests the _CompareValue function."""
    filter_object = filters.GreaterEqualOperator(arguments=['first', 'second'])

    result = filter_object._CompareValue(0, 10)
    self.assertFalse(result)

    result = filter_object._CompareValue(10, 10)
    self.assertTrue(result)

    result = filter_object._CompareValue(20, 10)
    self.assertTrue(result)


# TODO: add tests for Contains
# TODO: add tests for InSet
# TODO: add tests for Regexp
# TODO: add tests for RegexpInsensitive


if __name__ == "__main__":
  unittest.main()
