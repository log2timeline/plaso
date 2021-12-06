#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac wifi.log parser."""

import unittest

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02 00:10:15.000',
        'text': 'test-macbookpro newsyslog[50498]: logfile turned over'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_text = (
        '<kernel> wl0: powerChange: *** '
        'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02 00:11:02.378',
        'text': expected_text}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02 07:41:01.371',
        'text': (
            '<kernel> wl0: leaveModulePoweredForOffloads: Wi-Fi will stay on.')}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02 07:41:02.207',
        'text': (
            '<kernel> Setting BTCoex Config: enable_2G:1, profile_2g:0, '
            'enable_5G:1, profile_5G:0')}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

  def testParse(self):
    """Tests the Parse function."""
    parser = mac_wifi.MacWifiLogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['wifi.log'], parser, knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'Interface en0 turn up.',
        'agent': 'airportd[88]',
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14 20:36:37.222',
        'function': 'airportdProcessDLILEvent',
        'text': 'en0 attached (up)'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'action': 'Wifi connected to SSID CampusNet',
        'agent': 'airportd[88]',
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14 20:36:43.818',
        'function': '_doAutoJoin',
        'text': (
            'Already associated to \u201cCampusNet\u201d. Bailing on '
            'auto-join.')}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14 21:50:52.395',
        'text': (
            '<airportd[88]> _handleLinkEvent: Unable to process link event, '
            'op mode request returned -3903 (Operation not supported)')}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'action': (
            'New wifi configured. BSSID: 88:30:8a:7a:61:88, SSID: AndroidAP, '
            'Security: WPA2 Personal.'),
        'agent': 'airportd[88]',
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14 21:52:09.883',
        'function': '_processSystemPSKAssoc',
        'text': (
            'No password for network <CWNetwork: 0x7fdfe970b250> '
            '[ssid=AndroidAP, bssid=88:30:8a:7a:61:88, security=WPA2 '
            'Personal, rssi=-21, channel=<CWChannel: 0x7fdfe9712870> '
            '[channelNumber=11(2GHz), channelWidth={20MHz}], ibss=0] '
            'in the system keychain')}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-12-31 23:59:38.165'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2014-01-01 01:12:17.311'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
