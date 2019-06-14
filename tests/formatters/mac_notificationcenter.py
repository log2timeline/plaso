#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS NotificationCenter database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_notificationcenter

from tests.formatters import test_lib


class MacNotificationCenterFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MacOS NotificationCenter database event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_notificationcenter.MacNotificationCenterFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_notificationcenter.MacNotificationCenterFormatter()

    expected_attribute_names = [
        'bundle_name',
        'title',
        'subtitle',
        'body',
        'presented']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
