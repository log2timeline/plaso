#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac wifi.log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_wifi as _  # pylint: disable=unused-import
from plaso.parsers import mac_wifi

from tests.parsers import test_lib


class MacWifiUnitTest(test_lib.ParserTestCase):
  """Tests for the Mac wifi.log parser."""

  def testParseTurnedOver(self):
    """Tests the Parse function."""
    parser = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {'year': 2017}
    storage_writer = self._ParseFile(
        ['wifi_turned_over.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2017-01-02 00:10:15.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.text,
        'test-macbookpro newsyslog[50498]: logfile turned over')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2017-01-02 00:11:02.378000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_text = (
        '<kernel> wl0: powerChange: *** '
        'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')
    self.assertEqual(event_data.text, expected_text)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2017-01-02 07:41:01.371000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_string = (
        '<kernel> wl0: leaveModulePoweredForOffloads: Wi-Fi will stay on.')
    self.assertEqual(event_data.text, expected_string)

    event = events[5]

    self.CheckTimestamp(event.timestamp, '2017-01-02 07:41:02.207000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_text = (
        '<kernel> Setting BTCoex Config: enable_2G:1, profile_2g:0, '
        'enable_5G:1, profile_5G:0')
    self.assertEqual(event_data.text, expected_text)

  def testParse(self):
    """Tests the Parse function."""
    parser = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['wifi.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-14 20:36:37.222000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.agent, 'airportd[88]')
    self.assertEqual(event_data.function, 'airportdProcessDLILEvent')
    self.assertEqual(event_data.action, 'Interface en0 turn up.')
    self.assertEqual(event_data.text, 'en0 attached (up)')

    expected_message = (
        'Action: Interface en0 turn up. '
        'Agent: airportd[88] '
        '(airportdProcessDLILEvent) '
        'Log: en0 attached (up)')
    expected_short_message = (
        'Action: Interface en0 turn up.')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-11-14 20:36:43.818000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.agent, 'airportd[88]')
    self.assertEqual(event_data.function, '_doAutoJoin')
    self.assertEqual(event_data.action, 'Wifi connected to SSID CampusNet')

    expected_text = (
        'Already associated to \u201cCampusNet\u201d. Bailing on auto-join.')
    self.assertEqual(event_data.text, expected_text)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2013-11-14 21:50:52.395000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_string = (
        '<airportd[88]> _handleLinkEvent: Unable to process link event, '
        'op mode request returned -3903 (Operation not supported)')
    self.assertEqual(event_data.text, expected_string)

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2013-11-14 21:52:09.883000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.agent, 'airportd[88]')
    self.assertEqual(event_data.function, '_processSystemPSKAssoc')

    expected_action = (
        'New wifi configured. BSSID: 88:30:8a:7a:61:88, SSID: AndroidAP, '
        'Security: WPA2 Personal.')
    self.assertEqual(event_data.action, expected_action)

    expected_text = (
        'No password for network <CWNetwork: 0x7fdfe970b250> '
        '[ssid=AndroidAP, bssid=88:30:8a:7a:61:88, security=WPA2 '
        'Personal, rssi=-21, channel=<CWChannel: 0x7fdfe9712870> '
        '[channelNumber=11(2GHz), channelWidth={20MHz}], ibss=0] '
        'in the system keychain')
    self.assertEqual(event_data.text, expected_text)

    event = events[8]

    self.CheckTimestamp(event.timestamp, '2013-12-31 23:59:38.165000')

    event = events[9]

    self.CheckTimestamp(event.timestamp, '2014-01-01 01:12:17.311000')


if __name__ == '__main__':
  unittest.main()
