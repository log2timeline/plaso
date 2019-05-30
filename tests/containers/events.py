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
        'query']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class EventObjectTest(shared_test_lib.BaseTestCase):
  """Tests for the event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventObject()

    expected_attribute_names = [
        'data_type',
        'display_name',
        'filename',
        'hostname',
        'inode',
        'offset',
        'pathspec',
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
        'comment',
        'event_entry_index',
        'event_row_identifier',
        'event_stream_number',
        'labels']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
