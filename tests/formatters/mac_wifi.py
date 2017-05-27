#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X wifi.log file event formatter."""

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
        u'function',
        u'action',
        u'agent',
        u'text']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    date_time = dfdatetime_time_elements.TimeElements()
    date_time.CopyFromString(u'2016-11-14 20:36:37.222')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = u'mac:wifilog:line'
    event.action = u'Interface en0 turn up.'
    event.agent = u'airportd[88]'
    event.function = u'airportdProcessDLILEvent'
    event.text = u'en0 attached (up)'

    expected_messages = (
        u'Action: Interface en0 turn up. '
        u'Agent: airportd[88] '
        u'(airportdProcessDLILEvent) '
        u'Log: en0 attached (up)',
        u'Action: Interface en0 turn up.')

    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)

    date_time = dfdatetime_time_elements.TimeElements()
    date_time.CopyFromString(u'2017-01-02 00:10:15')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = u'mac:wifilog:line'
    event.text = u'test-macbookpro newsyslog[50498]: logfile turned over'

    expected_messages = (
        u'Log: test-macbookpro newsyslog[50498]: logfile turned over',
        u'Log: test-macbookpro newsyslog[50498]: logfile turned over')

    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
