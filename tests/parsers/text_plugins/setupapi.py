#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows SetupAPI log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import setupapi

from tests.parsers.text_plugins import test_lib


class SetupAPILogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Windows SetupAPI log text parser plugin."""

  def testProcessWithDevLog(self):
    """Tests the Process function with setupapi.dev.log."""
    plugin = setupapi.SetupAPILogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['setupapi.dev.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 388)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:59:28.110'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2016-10-05T11:16:03.747'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2016-10-05T11:16:16.471',
        'entry_type': (
            'Device Install (Hardware initiated) - SWD\\IP_TUNNEL_VBUS'
            '\\Teredo_Tunnel_Device')}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2016-10-12T03:36:30.998',
        'entry_type': (
            'Device Install (DiInstallDriver) - C:\\Windows\\System32'
            '\\DriverStore\\FileRepository\\prnms003.inf_x86_8f17aac186c70ea6'
            '\\prnms003.inf'),
        'exit_status': 'SUCCESS'}

    self.CheckEventValues(storage_writer, events[57], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2016-11-22T23:50:30.938',
        'entry_type': (
            'Device Install (Hardware initiated) - SWD\\WPDBUSENUM'
            '\\_??_USBSTOR#Disk&Ven_Generic&Prod_Flash_Disk&Rev_8.07#99E2116A&0'
            '#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}')}

    self.CheckEventValues(storage_writer, events[386], expected_event_values)

  def testProcessWithSetupLog(self):
    """Tests the Process function with setupapi.setup.log."""
    plugin = setupapi.SetupAPILogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['setupapi.setup.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 32)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:53:16.599',
        'timestamp': '2015-11-22 17:53:16.599000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:53:28.973'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:53:29.305',
        'entry_type': 'Setup Plug and Play Device Install'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:53:43.429',
        'entry_type': (
            'Setup online Device Install (Hardware initiated) - SW'
            '\\{97ebaacc-95bd-11d0-a3ea-00a0c9223196}'
            '\\{53172480-4791-11D0-A5D6-28DB04C10000}')}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:57:17.502',
        'entry_type': (
            'Setup Import Driver Package - C:\\Windows\\system32'
            '\\spool\\tools\\Microsoft XPS Document Writer\\prnms001.Inf')}

    self.CheckEventValues(storage_writer, events[30], expected_event_values)

  def testProcessWithSetupLogAndTimeZone(self):
    """Tests the Process function with setupapi.setup.log and a time zone."""
    plugin = setupapi.SetupAPILogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['setupapi.setup.log'], plugin, time_zone_string='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 32)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'date_time': '2015-11-22T17:53:16.599',
        'timestamp': '2015-11-22 16:53:16.599000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
