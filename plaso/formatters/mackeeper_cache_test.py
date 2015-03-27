#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MacKeeper Cache event formatter."""

import unittest

from plaso.formatters import mackeeper_cache
from plaso.formatters import test_lib


class MacKeeperCacheFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MacKeeper Cache event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mackeeper_cache.MacKeeperCacheFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mackeeper_cache.MacKeeperCacheFormatter()

    expected_attribute_names = [
        u'description',
        u'event_type',
        u'text',
        u'url',
        u'record_id',
        u'room']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
