#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the apache access log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import apache_access
from tests.formatters import test_lib


class ApacheAccessFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the apache access log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = apache_access.ApacheAccessFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = apache_access.ApacheAccessFormatter()

    expected_attribute_names = [
        'http_request',
        'ip_address',
        'http_response_code',
        'http_request_referer',
        'http_request_user_agent',
        'port_number',
        'server_name'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
