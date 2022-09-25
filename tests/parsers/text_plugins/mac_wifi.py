#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac wifi.log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import mac_wifi

from tests.parsers.text_plugins import test_lib


class MacWifiLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Mac wifi.log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = mac_wifi.MacWifiLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['wifi.log'], plugin, knowledge_base_values={'year': 2013})

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'Interface en0 turn up.',
        'agent': 'airportd[88]',
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14T20:36:37.222+00:00',
        'function': 'airportdProcessDLILEvent',
        'text': 'en0 attached (up)'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'action': 'Wifi connected to SSID CampusNet',
        'agent': 'airportd[88]',
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14T20:36:43.818+00:00',
        'function': '_doAutoJoin',
        'text': (
            'Already associated to \u201cCampusNet\u201d. Bailing on '
            'auto-join.')}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2013-11-14T21:50:52.395+00:00',
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
        'date_time': '2013-11-14T21:52:09.883+00:00',
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
        'date_time': '2013-12-31T23:59:38.165+00:00'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2014-01-01T01:12:17.311+00:00'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

  def testProcessWithTurnedOverLog(self):
    """Tests the Process function with a turned over log file."""
    plugin = mac_wifi.MacWifiLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['wifi_turned_over.log'], plugin, knowledge_base_values={'year': 2017})

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02T00:10:15.000+00:00',
        'text': 'test-macbookpro newsyslog[50498]: logfile turned over'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_text = (
        '<kernel> wl0: powerChange: *** '
        'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02T00:11:02.378+00:00',
        'text': expected_text}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02T07:41:01.371+00:00',
        'text': (
            '<kernel> wl0: leaveModulePoweredForOffloads: Wi-Fi will stay on.')}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:wifilog:line',
        'date_time': '2017-01-02T07:41:02.207+00:00',
        'text': (
            '<kernel> Setting BTCoex Config: enable_2G:1, profile_2g:0, '
            'enable_5G:1, profile_5G:0')}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()
