#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry AppCompatCache entries event formatter."""

from __future__ import unicode_literals

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
        'key_path', 'entry_index', 'path']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
