#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SRUM ESE database event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import srum

from tests.formatters import test_lib


class SRUMNetworkDataUsageMonitorEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the SRUM network data usage monitor event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = srum.SRUMNetworkDataUsageMonitorEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = srum.SRUMNetworkDataUsageMonitorEventFormatter()

    expected_attribute_names = [
        'application_identifier',
        'bytes_received',
        'bytes_sent',
        'interface_luid',
        'user_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
