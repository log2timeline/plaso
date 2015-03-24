#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iPod device event formatter."""

import unittest

from plaso.formatters import ipod
from plaso.formatters import test_lib


class IPodDeviceFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the iPod device event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ipod.IPodDeviceFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ipod.IPodDeviceFormatter()

    expected_attribute_names = [
      u'device_id',
      u'device_class',
      u'family_id',
      u'use_count',
      u'serial_number',
      u'imei']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
