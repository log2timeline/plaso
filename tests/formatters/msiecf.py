#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIECF event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msiecf

from tests.formatters import test_lib


class MsiecfLeakFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF leak item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfLeakFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


class MsiecfUrlFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF URL item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfUrlFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
