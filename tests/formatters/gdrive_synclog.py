#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive sync log event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import gdrive_synclog

from tests.formatters import test_lib


class GoogleDriveSyncLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Drive sync log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = gdrive_synclog.GoogleDriveSyncLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = gdrive_synclog.GoogleDriveSyncLogFormatter()

    expected_attribute_names = [
        'log_level',
        'pid',
        'thread',
        'source_code',
        'message']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
