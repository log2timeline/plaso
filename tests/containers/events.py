#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event attribute containers."""

import unittest

from plaso.containers import events

from tests import test_lib as shared_test_lib


class EventValuesHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the event values helper functions."""

  def testCalculateEventValuesHash(self):
    """Tests the CalculateEventValuesHash function."""
    event_data = events.EventData()
    event_data.data_type = 'test'
    event_data.attribute1 = 'attribute1'
    event_data.attribute2 = 10
    event_data.attribute3 = ['attribute1']

    event_data_stream = events.EventDataStream()
    event_data_stream.attribute1 = 'ATTR1'
    event_data_stream.attribute2 = 99

    content_identifier = events.CalculateEventValuesHash(
        event_data, event_data_stream)

    self.assertEqual(content_identifier, '31aac7b1f8c1446f4b638c0dc5f92981')


class EventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventData()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'data_type']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)

  def testGetAttributes(self):
    """Tests the GetAttributes function."""
    attribute_container = events.EventData()

    with self.assertRaises(TypeError):
      attribute_container.error = b'bytes'
      attribute_container.GetAttributeValuesHash()

    with self.assertRaises(TypeError):
      attribute_container.error = {'key': 'value'}
      attribute_container.GetAttributeValuesHash()

  def testGetEventDataStreamIdentifier(self):
    """Tests the GetEventDataStreamIdentifier function."""
    attribute_container = events.EventData()

    identifier = attribute_container.GetEventDataStreamIdentifier()
    self.assertIsNone(identifier)

  def testSetEventDataStreamIdentifier(self):
    """Tests the SetEventDataStreamIdentifier function."""
    attribute_container = events.EventData()

    attribute_container.SetEventDataStreamIdentifier(None)


class EventDataStreamTest(shared_test_lib.BaseTestCase):
  """Tests for the event data stream attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventDataStream()

    expected_attribute_names = [
        'file_entropy',
        'md5_hash',
        'path_spec',
        'sha1_hash',
        'sha256_hash',
        'yara_match']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class EventObjectTest(shared_test_lib.BaseTestCase):
  """Tests for the event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventObject()

    expected_attribute_names = [
        '_event_data_identifier',
        'date_time',
        'timestamp',
        'timestamp_desc']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)

  def testGetEventDataIdentifier(self):
    """Tests the GetEventDataIdentifier function."""
    attribute_container = events.EventObject()

    identifier = attribute_container.GetEventDataIdentifier()
    self.assertIsNone(identifier)

  def testSetEventDataIdentifier(self):
    """Tests the SetEventDataIdentifier function."""
    attribute_container = events.EventObject()

    attribute_container.SetEventDataIdentifier(None)


class EventTagTest(shared_test_lib.BaseTestCase):
  """Tests for the event tag attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventTag()

    expected_attribute_names = [
        '_event_identifier',
        'labels']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)

  def testGetEventIdentifier(self):
    """Tests the GetEventIdentifier function."""
    attribute_container = events.EventTag()

    identifier = attribute_container.GetEventIdentifier()
    self.assertIsNone(identifier)

  def testSetEventIdentifier(self):
    """Tests the SetEventIdentifier function."""
    attribute_container = events.EventTag()

    attribute_container.SetEventIdentifier(None)


class YearLessLogHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the year-less log helper attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.YearLessLogHelper()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        'earliest_year',
        'last_relative_year',
        'latest_year']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)

  def testGetEventDataStreamIdentifier(self):
    """Tests the GetEventDataStreamIdentifier function."""
    attribute_container = events.YearLessLogHelper()

    identifier = attribute_container.GetEventDataStreamIdentifier()
    self.assertIsNone(identifier)

  def testSetEventDataStreamIdentifier(self):
    """Tests the SetEventDataStreamIdentifier function."""
    attribute_container = events.YearLessLogHelper()

    attribute_container.SetEventDataStreamIdentifier(None)


if __name__ == '__main__':
  unittest.main()
