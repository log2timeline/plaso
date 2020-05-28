#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event attribute containers."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events

from tests import test_lib as shared_test_lib


class EventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventData()

    expected_attribute_names = [
        'data_type',
        'offset',
        'parser',
        'query']

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


class EventObjectTest(shared_test_lib.BaseTestCase):
  """Tests for the event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventObject()

    expected_attribute_names = [
        '_event_data_row_identifier',
        'parser',
        'tag',
        'timestamp',
        'timestamp_desc']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class EventTagTest(shared_test_lib.BaseTestCase):
  """Tests for the event tag attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventTag()

    expected_attribute_names = [
        '_event_row_identifier',
        'comment',
        'labels']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
