#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the plist event attribute containers."""

import unittest

from plaso.containers import plist_event

from tests import test_lib as shared_test_lib


class PlistEventTest(shared_test_lib.BaseTestCase):
  """Tests for the plist event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = plist_event.PlistEvent(None, None, 0)

    expected_attribute_names = [
        u'data_type', u'desc', u'display_name', u'filename', u'hostname',
        u'inode', u'key', u'offset', u'pathspec', u'root', u'tag',
        u'timestamp', u'timestamp_desc', u'username']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class PlistTimeEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the plist event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = plist_event.PlistTimeEventData()

    expected_attribute_names = [
        u'data_type', u'desc', u'hostname', u'key', u'offset', u'query',
        u'root', u'username']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
