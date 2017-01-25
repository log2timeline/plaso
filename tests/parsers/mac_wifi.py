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
    parser_object = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {u'year': 2017}
    storage_writer = self._ParseFile(
        [u'wifi_turned_over.log'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 6)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 00:10:15')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.body,
                     u'test-macbookpro newsyslog[50498]: logfile turned over')

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 00:11:02.378')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_text = (
        u'<kernel> wl0: powerChange: *** '
        u'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')
    self.assertEqual(event_object.body, expected_text)

    event_object = storage_writer.events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 07:41:01.371')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'<kernel> wl0: leaveModulePoweredForOffloads: Wi-Fi will stay on.')
    self.assertEqual(event_object.body, expected_string)

    event_object = storage_writer.events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-02 07:41:02.207')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_text = (
        u'<kernel> Setting BTCoex Config: enable_2G:1, profile_2g:0, '
        u'enable_5G:1, profile_5G:0')

    self.assertEqual(event_object.body, expected_text)

  @shared_test_lib.skipUnlessHasTestFile([u'wifi.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'wifi.log'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 10)

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 20:36:37.222')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.body,
        u'<airportd[88]> airportdProcessDLILEvent: en0 attached (up)')

    event_object = storage_writer.events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 20:36:43.818')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_text = (
        u'<airportd[88]> _doAutoJoin: Already associated to “CampusNet”. '
        u'Bailing on auto-join.')
    self.assertEqual(event_object.body, expected_text)

    event_object = storage_writer.events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 21:50:52.395')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'<airportd[88]> _handleLinkEvent: Unable to process link event, '
        u'op mode request returned -3903 (Operation not supported)')

    self.assertEqual(event_object.body, expected_string)

    event_object = storage_writer.events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 21:52:09.883')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_text = (
        u'<airportd[88]> _processSystemPSKAssoc: No password for network '
        u'<CWNetwork: 0x7fdfe970b250> [ssid=AndroidAP, '
        u'bssid=88:30:8a:7a:61:88, security=WPA2 Personal, rssi=-21, '
        u'channel=<CWChannel: 0x7fdfe9712870> [channelNumber=11(2GHz), '
        u'channelWidth={20MHz}], ibss=0] in the system keychain')

    self.assertEqual(event_object.body, expected_text)

    event_object = storage_writer.events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:38.165')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = storage_writer.events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-01 01:12:17.311')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
