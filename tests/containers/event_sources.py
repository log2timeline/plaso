#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event source attribute containers."""

import unittest

from plaso.containers import event_sources

from tests import test_lib as shared_test_lib


class EventSourceTest(shared_test_lib.BaseTestCase):
  """Tests for the event source attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = event_sources.EventSource()

    expected_attribute_names = [
        'data_type', 'file_entry_type', 'path_spec']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class FileEntryEventSourceTest(shared_test_lib.BaseTestCase):
  """Tests for the file entry event source attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = event_sources.FileEntryEventSource()

    expected_attribute_names = [
        'data_type', 'file_entry_type', 'path_spec']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
