#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event attribute containers."""

import unittest

from plaso.containers import events

from tests import test_lib as shared_test_lib


class EventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventData()

    expected_attribute_names = [
        '_event_data_stream_row_identifier',
        'data_type',
        'parser']

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
        '_event_data_row_identifier',
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

    expected_attribute_names = ['_event_row_identifier', 'labels']

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


if __name__ == '__main__':
  unittest.main()
