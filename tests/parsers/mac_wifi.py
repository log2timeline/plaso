#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac wifi.log parser."""

import unittest

from plaso.formatters import mac_wifi  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import mac_wifi

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacWifiUnitTest(test_lib.ParserTestCase):
  """Tests for the Mac wifi.log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'wifi_turned_over.log'])
  def testParseTurnedOver(self):
    """Tests the Parse function."""
    parser = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {u'year': 2017}
    storage_writer = self._ParseFile(
        [u'wifi_turned_over.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 00:10:15')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.text,
        u'test-macbookpro newsyslog[50498]: logfile turned over')

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 00:11:02.378')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_text = (
        u'<kernel> wl0: powerChange: *** '
        u'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')
    self.assertEqual(event.text, expected_text)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 07:41:01.371')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_string = (
        u'<kernel> wl0: leaveModulePoweredForOffloads: Wi-Fi will stay on.')
    self.assertEqual(event.text, expected_string)

    event = events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 07:41:02.207')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_text = (
        u'<kernel> Setting BTCoex Config: enable_2G:1, profile_2g:0, '
        u'enable_5G:1, profile_5G:0')

    self.assertEqual(event.text, expected_text)

  @shared_test_lib.skipUnlessHasTestFile([u'wifi.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'wifi.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 20:36:37.222')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.agent, u'airportd[88]')
    self.assertEqual(event.function, u'airportdProcessDLILEvent')
    self.assertEqual(event.action, u'Interface en0 turn up.')
    self.assertEqual(event.text, u'en0 attached (up)')

    expected_message = (
        u'Action: Interface en0 turn up. '
        u'Agent: airportd[88] '
        u'(airportdProcessDLILEvent) '
        u'Log: en0 attached (up)')
    expected_short_message = (
        u'Action: Interface en0 turn up.')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 20:36:43.818')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.agent, u'airportd[88]')
    self.assertEqual(event.function, u'_doAutoJoin')
    self.assertEqual(event.action, u'Wifi connected to SSID CampusNet')

    expected_text = (
        u'Already associated to \u201cCampusNet\u201d. Bailing on auto-join.')
    self.assertEqual(event.text, expected_text)

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 21:50:52.395')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_string = (
        u'<airportd[88]> _handleLinkEvent: Unable to process link event, '
        u'op mode request returned -3903 (Operation not supported)')

    self.assertEqual(event.text, expected_string)

    event = events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 21:52:09.883')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(u'airportd[88]', event.agent)
    self.assertEqual(u'_processSystemPSKAssoc', event.function)

    expected_action = (
        u'New wifi configured. BSSID: 88:30:8a:7a:61:88, SSID: AndroidAP, '
        u'Security: WPA2 Personal.')

    self.assertEqual(event.action, expected_action)

    expected_text = (
        u'No password for network <CWNetwork: 0x7fdfe970b250> '
        u'[ssid=AndroidAP, bssid=88:30:8a:7a:61:88, security=WPA2 '
        u'Personal, rssi=-21, channel=<CWChannel: 0x7fdfe9712870> '
        u'[channelNumber=11(2GHz), channelWidth={20MHz}], ibss=0] '
        u'in the system keychain')

    self.assertEqual(event.text, expected_text)

    event = events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:38.165')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-01 01:12:17.311')
    self.assertEqual(event.timestamp, expected_timestamp)

if __name__ == '__main__':
  unittest.main()
