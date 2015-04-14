#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows event formatter."""

import unittest

from plaso.formatters import test_lib
from plaso.formatters import windows


class WindowsVolumeCreationEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows volume creation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = windows.WindowsVolumeCreationEventFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = windows.WindowsVolumeCreationEventFormatter()

    expected_attribute_names = [
        u'device_path',
        u'serial_number',
        u'origin']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
