#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the TeamViewer log parser."""

import unittest

from plaso.parsers.text_plugins import teamviewer

from tests.parsers.text_plugins import test_lib


class TeamViewerApplicationLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the TeamViewer application log text file parser plugin."""

  _TEST_BODY = """\
Start:              2024/02/16 06:05:19.548 (UTC-8:00)
Version:            15.50.5 (64-bit)
Version short hash: b23ae08066e
ID:                 0
Loglevel:           Info
License:            0
IC:                 -2100253538
CPU:                AMD64 Family 23 Model 113 Stepping 0, AuthenticAMD
CPU extensions:     e9
OS:                 Win_10.0.17763_W (64-bit)
IP:                 10.0.2.15
MID:                0x080027e6e559_1d44cc67230d0d5_3030843078
MIDv:               0
Proxy-Settings:     Type=1 IP= User=
IE                  11.1790.17763.0
AppPath:            C:\\Program Files\\TeamViewer\\TeamViewer_Service.exe
UserAccount:        SYSTEM"""

  def testProcess(self):
    """Tests the Process function."""
    plugin = teamviewer.TeamViewerApplicationLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['teamviewer', 'TeamViewer15_Logfile.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1013)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values_multi_line = {
        'body': self._TEST_BODY,
        'process_identifier': 2136,
        'recorded_time': '2024-02-16T06:05:19.561+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 17)
    self.CheckEventData(event_data, expected_event_values_multi_line)

    expected_event_values_single_line = {
        'body': 'MDV2: IsDeviceManagementEnabled: mdv2: 1 management: 1',
        'process_identifier': 5276,
        'recorded_time': '2024-02-16T06:18:36.370+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1012)
    self.CheckEventData(event_data, expected_event_values_single_line)


class TeamViewerConnectionsIncomingLogTextPluginTest(
    test_lib.TextPluginTestCase):
  """Tests for the TeamViewer connections_incoming.txt log parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = teamviewer.TeamViewerConnectionsIncomingLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['teamviewer', 'connections_incoming.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_type': 'RemoteControl',
        'connection_identifier': '{b3a4df33-d027-44d5-b50f-4e61115494d4}',
        'data_type': 'teamviewer:connections_incoming:entry',
        'display_name': 'TestUserRedacted',
        'end_time': '2024-02-16T14:18:36+00:00',
        'local_account': 'IEUser',
        'source_identifier': 1660360496,
        'start_time': '2024-02-16T14:16:32+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TeamViewerConnectionsOutgoingLogTextPluginTest(
    test_lib.TextPluginTestCase):
  """Tests for the TeamViewer Connections.txt log file parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = teamviewer.TeamViewerConnectionsOutgoingLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['teamviewer', 'Connections.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_type': 'RemoteControl',
        'connection_identifier': '{b35110b2-7dc5-4bb9-8d54-ca80953f65f8}',
        'data_type': 'teamviewer:connections_outgoing:entry',
        'destination_identifier': 1660360496,
        'end_time': '2024-02-20T13:11:52+00:00',
        'local_account': 'IEUser',
        'start_time': '2024-02-20T13:10:33+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
