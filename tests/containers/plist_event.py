#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the plist event attribute containers."""

import unittest

from plaso.containers import plist_event

from tests import test_lib as shared_test_lib


class PlistTimeEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the plist event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = plist_event.PlistTimeEventData()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'data_type',
        'key',
        'root',
        'written_time']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
