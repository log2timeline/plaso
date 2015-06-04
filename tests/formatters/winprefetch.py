#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Prefetch event formatter."""

import unittest

from plaso.formatters import winprefetch

from tests.formatters import test_lib


class WinPrefetchExecutionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Prefetch execution event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winprefetch.WinPrefetchExecutionFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winprefetch.WinPrefetchExecutionFormatter()

    expected_attribute_names = [
        u'executable',
        u'run_count',
        u'path',
        u'prefetch_hash',
        u'volumes_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
