#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iPod device event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ipod

from tests.formatters import test_lib


class IPodDeviceFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the iPod device event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ipod.IPodDeviceFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ipod.IPodDeviceFormatter()

    expected_attribute_names = [
        'device_id',
        'device_class',
        'family_id',
        'use_count',
        'serial_number',
        'imei']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
