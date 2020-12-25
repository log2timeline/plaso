#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shell item event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import shell_items

from tests.formatters import test_lib


class ShellItemFileEntryEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the shell item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = shell_items.ShellItemFileEntryEventFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
