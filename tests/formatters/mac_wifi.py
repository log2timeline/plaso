#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X wifi.log file event formatter."""

import unittest

from plaso.formatters import mac_wifi
from plaso.parsers import mac_wifi as mac_wifi_parser

from tests.formatters import test_lib


class MacWifiLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the wifi.log file event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._formatter = mac_wifi.MacWifiLogFormatter()

  def testInitialization(self):
    """Tests the initialization."""
    self.assertIsNotNone(self._formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""

    expected_attribute_names = [
        u'function',
        u'action',
        u'agent',
        u'text']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    mediator = None
    event = mac_wifi_parser.MacWifiLogEvent(
        u'Thu Nov 14 20:36:37.222', u'airportd[88]',
        u'airportdProcessDLILEvent',
        u'en0 attached (up)', u'Interface en0 turn up.')

    expected_messages = (
        u'Action: Interface en0 turn up. '
        u'Agent: airportd[88] '
        u'(airportdProcessDLILEvent) '
        u'Log: en0 attached (up)',
        u'Action: Interface en0 turn up.')

    messages = self._formatter.GetMessages(mediator, event)
    self.assertEqual(messages, expected_messages)

  def testGetMessagesTurnedOver(self):
    """Tests the GetMessages method for turned over logfile."""
    mediator = None
    event = mac_wifi_parser.MacWifiLogEvent(
        u'2017-01-02 00:10:15', u'', u'',
        u'test-macbookpro newsyslog[50498]: logfile turned over', u'')

    expected_messages = (
        u'Log: test-macbookpro newsyslog[50498]: logfile turned over',
        u'Log: test-macbookpro newsyslog[50498]: logfile turned over')

    messages = self._formatter.GetMessages(mediator, event)
    self.assertEqual(messages, expected_messages)

if __name__ == '__main__':
  unittest.main()
