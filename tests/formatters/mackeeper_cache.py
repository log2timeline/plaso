#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the MacKeeper Cache event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mackeeper_cache

from tests.formatters import test_lib


class MacKeeperCacheFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MacKeeper Cache event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mackeeper_cache.MacKeeperCacheFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mackeeper_cache.MacKeeperCacheFormatter()

    expected_attribute_names = [
        'description',
        'event_type',
        'text',
        'url',
        'record_id',
        'room']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
