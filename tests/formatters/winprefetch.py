#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Prefetch event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winprefetch

from tests.formatters import test_lib


class WinPrefetchExecutionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Prefetch execution event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winprefetch.WinPrefetchExecutionFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
