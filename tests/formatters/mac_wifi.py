#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS wifi.log file event formatter."""

from __future__ import unicode_literals

import unittest

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import time_events
from plaso.formatters import mac_wifi
from plaso.lib import definitions

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
        'function',
        'action',
        'agent',
        'text']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    date_time = dfdatetime_time_elements.TimeElements()
    date_time.CopyFromDateTimeString('2016-11-14 20:36:37.222')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = 'mac:wifilog:line'
    event.action = 'Interface en0 turn up.'
    event.agent = 'airportd[88]'
    event.function = 'airportdProcessDLILEvent'
    event.text = 'en0 attached (up)'

    expected_messages = (
        'Action: Interface en0 turn up. '
        'Agent: airportd[88] '
        '(airportdProcessDLILEvent) '
        'Log: en0 attached (up)',
        'Action: Interface en0 turn up.')

    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)

    date_time = dfdatetime_time_elements.TimeElements()
    date_time.CopyFromDateTimeString('2017-01-02 00:10:15')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = 'mac:wifilog:line'
    event.text = 'test-macbookpro newsyslog[50498]: logfile turned over'

    expected_messages = (
        'Log: test-macbookpro newsyslog[50498]: logfile turned over',
        'Log: test-macbookpro newsyslog[50498]: logfile turned over')

    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
