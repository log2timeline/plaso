#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft IIS log file event formatter."""

import unittest

from plaso.formatters import iis

from tests.formatters import test_lib


class IISLogFileEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Microsoft IIS log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = iis.IISLogFileEventFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = iis.IISLogFileEventFormatter()

    expected_attribute_names = [
        u'http_method', u'requested_uri_stem', u'source_ip', u'dest_ip',
        u'dest_port', u'http_status', u'sent_bytes', u'received_bytes',
        u'user_agent', u'protocol_version']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
