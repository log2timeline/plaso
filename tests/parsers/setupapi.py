#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Setupapi log parser."""

import unittest

from plaso.parsers import setupapi

from tests.parsers import test_lib


class SetupapiLogUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows Setupapi log parser.

  Since Setupapi logs record in local time, these tests assume that the local
  timezone is set to UTC.
  """

  def testParseDevLog(self):
    """Tests the Parse function on setupapi.dev.log."""
    parser = setupapi.SetupapiLogParser()
    storage_writer = self._ParseFile(['setupapi.dev.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 388)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2015-11-22 17:59:28.110000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'timestamp': '2016-10-05 11:16:03.747000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'timestamp': '2016-10-05 11:16:16.471000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_message = (
        'Device Install (Hardware initiated) - SWD\\IP_TUNNEL_VBUS'
        '\\Teredo_Tunnel_Device')
    expected_short_message = (
        'Device Install (Hardware initiated) - SWD\\IP_TUNNEL_VBUS'
        '\\Teredo_Tunnel_Device')

    event_data = self._GetEventDataOfEvent(storage_writer, events[4])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_message = (
        'Device Install (DiInstallDriver) - C:\\Windows\\System32'
        '\\DriverStore\\FileRepository\\prnms003.inf_x86_8f17aac186c70ea6'
        '\\prnms003.inf - SUCCESS')
    expected_short_message = (
        'SUCCESS - Device Install (DiInstallDriver) - C:\\Windows\\System32'
        '\\DriverStore\\...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[57])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2016-11-22 23:50:30.938000'}

    self.CheckEventValues(storage_writer, events[386], expected_event_values)

    expected_message = (
        'Device Install (Hardware initiated) - SWD\\WPDBUSENUM'
        '\\_??_USBSTOR#Disk&Ven_Generic&Prod_Flash_Disk&Rev_8.07#99E2116A&0'
        '#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}')
    expected_short_message = (
        'Device Install (Hardware initiated) - SWD\\WPDBUSENUM'
        '\\_??_USBSTOR#Disk&Ven_Gen...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[386])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseSetupLog(self):
    """Tests the Parse function on setupapi.setup.log."""
    parser = setupapi.SetupapiLogParser()
    storage_writer = self._ParseFile(['setupapi.setup.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 32)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2015-11-22 17:53:16.599000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'timestamp': '2015-11-22 17:53:28.973000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'timestamp': '2015-11-22 17:53:29.305000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_message = 'Setup Plug and Play Device Install'
    expected_short_message = 'Setup Plug and Play Device Install'

    event_data = self._GetEventDataOfEvent(storage_writer, events[4])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_message = (
        'Setup online Device Install (Hardware initiated) - SW'
        '\\{97ebaacc-95bd-11d0-a3ea-00a0c9223196}'
        '\\{53172480-4791-11D0-A5D6-28DB04C10000}')
    expected_short_message = (
        'Setup online Device Install (Hardware initiated) - SW'
        '\\{97ebaacc-95bd-11d0-a3e...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[14])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2015-11-22 17:57:17.502000'}

    self.CheckEventValues(storage_writer, events[30], expected_event_values)

    expected_message = (
        'Setup Import Driver Package - C:\\Windows\\system32'
        '\\spool\\tools\\Microsoft XPS Document Writer\\prnms001.Inf')
    expected_short_message = (
        'Setup Import Driver Package - C:\\Windows\\system32\\spool'
        '\\tools\\Microsoft XPS D...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[30])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseSetupLogWithTimeZone(self):
    """Tests the Parse function on setupapi.setup.log with a time zone."""
    parser = setupapi.SetupapiLogParser()
    storage_writer = self._ParseFile(
        ['setupapi.setup.log'], parser, timezone='CET')

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 32)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2015-11-22 16:53:16.599000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
