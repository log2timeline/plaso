#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox history event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox

from tests.formatters import test_lib


class FirefoxPageVisitFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxPageVisitFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
