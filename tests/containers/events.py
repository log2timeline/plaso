#!/usr/bin/python
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

    expected_attribute_names = [u'data_type', u'offset', u'query']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class EventObjectTest(shared_test_lib.BaseTestCase):
  """Tests for the event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventObject()

    expected_attribute_names = [
        u'data_type', u'display_name', u'filename', u'hostname', u'inode',
        u'offset', u'pathspec', u'tag', u'timestamp']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class EventTagTest(shared_test_lib.BaseTestCase):
  """Tests for the event tag attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = events.EventTag()

    expected_attribute_names = [
        u'comment', u'event_entry_index', u'event_stream_number', u'labels']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
