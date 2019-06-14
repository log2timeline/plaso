#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft IIS log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import iis

from tests.formatters import test_lib


class IISLogFileEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Microsoft IIS log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = iis.IISLogFileEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = iis.IISLogFileEventFormatter()

    expected_attribute_names = [
        'http_method', 'requested_uri_stem', 'source_ip', 'dest_ip',
        'dest_port', 'http_status', 'sent_bytes', 'received_bytes',
        'user_agent', 'protocol_version']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
