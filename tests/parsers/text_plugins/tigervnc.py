#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the TigerVNC log file text parser plugin."""

import unittest

from plaso.parsers.text_plugins import tigervnc

from tests.parsers.text_plugins import test_lib


class TigerVNCLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the TigerVNC log file text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = tigervnc.TigerVNCLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['tigervnc.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test first event
    expected_event_values = {
        'added_time': '2016-06-05T10:30:45',
        'component': 'XserverDesktop',
        'data_type': 'tigervnc:log',
        'text': (
            'Listening for VNC connections on local interface(s), port 5900')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test event with client connection
    expected_event_values = {
        'added_time': '2016-06-05T10:31:12',
        'component': 'VNCServerST',
        'data_type': 'tigervnc:log',
        'text': 'Client connection from 192.168.1.5'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Test multi-line event (last event)
    expected_event_values = {
        'added_time': '2016-06-10T14:31:00',
        'component': 'VNCServerST',
        'data_type': 'tigervnc:log',
        'text': (
            'rfbProcessClientNormalMessage: ignoring unknown encoding type 307')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
