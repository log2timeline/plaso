#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SRUM ESE database event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import srum

from tests.formatters import test_lib


class SRUMApplicationResourceUsageEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the SRUM application resource usage event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = srum.SRUMApplicationResourceUsageEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = srum.SRUMApplicationResourceUsageEventFormatter()

    expected_attribute_names = [
        'application']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SRUMNetworkDataUsageEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SRUM network data usage event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = srum.SRUMNetworkDataUsageEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = srum.SRUMNetworkDataUsageEventFormatter()

    expected_attribute_names = [
        'application',
        'bytes_received',
        'bytes_sent',
        'interface_luid',
        'user_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SRUMNetworkConnectivityUsageEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the SRUM network connectivity usage event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = srum.SRUMNetworkConnectivityUsageEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = srum.SRUMNetworkConnectivityUsageEventFormatter()

    expected_attribute_names = [
        'application']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
