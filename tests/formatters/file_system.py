#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file system event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import file_system

from tests.formatters import test_lib


class NTFSFileStatEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the NFTS file system stat event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = file_system.NTFSFileStatEventFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


class NTFSUSNChangeEventFormatter(test_lib.EventFormatterTestCase):
  """Tests for the NTFS USN change event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = file_system.NTFSUSNChangeEventFormatter()
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
