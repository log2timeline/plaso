#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry AppCompatCache entries event formatter."""

import unittest

from plaso.formatters import appcompatcache

from tests.formatters import test_lib


class AppCompatCacheFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the AppCompatCache Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = appcompatcache.AppCompatCacheFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = appcompatcache.AppCompatCacheFormatter()

    expected_attribute_names = [
        u'key_path', u'entry_index', u'path']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
