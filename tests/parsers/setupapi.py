#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Setupapi log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import setupapi as _  # pylint: disable=unused-import
from plaso.parsers import setupapi

from tests.parsers import test_lib


class SetupapiLogUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows Setupapi log parser.

  Since Setupapi logs record in local time, these tests assume that the local
  timezone is set to UTC.
  """

  def testParseDevLog(self):
    """Tests the Parse function on dev log."""
    parser = setupapi.SetupapiLogParser()
    storage_writer = self._ParseFile(['setupapi.dev.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 194)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-11-22 17:59:28.110000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2016-10-05 11:16:03.747000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2016-10-05 11:16:16.471000')

    expected_message = (
        'Description: Device Install (Hardware initiated) - SWD\\IP_TUNNEL_VBUS'
        '\\Teredo_Tunnel_Device | Exit status: SUCCESS')
    expected_short_message = (
        'Device Install (Hardware initiated) - SWD\\IP_TUNNEL_VBUS'
        '\\Teredo_Tunnel_Device')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[28]
    expected_message = (
        'Description: Device Install (DiInstallDriver) - C:\\Windows\\System32'
        '\\DriverStore\\FileRepository\\prnms003.inf_x86_8f17aac186c70ea6'
        '\\prnms003.inf | Exit status: SUCCESS')
    expected_short_message = (
        'Device Install (DiInstallDriver) - C:\\Windows\\System32\\DriverStore'
        '\\FileReposi...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[193]

    self.CheckTimestamp(event.timestamp, '2016-11-22 23:50:30.938000')

    expected_message = (
        'Description: Device Install (Hardware initiated) - SWD\\WPDBUSENUM'
        '\\_??_USBSTOR#Disk&Ven_Generic&Prod_Flash_Disk&Rev_8.07#99E2116A&0'
        '#{53f56307-b6bf-11d0-94f2-00a0c91efb8b} | Exit status: SUCCESS')
    expected_short_message = (
        'Device Install (Hardware initiated) - SWD\\WPDBUSENUM'
        '\\_??_USBSTOR#Disk&Ven_Gen...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  def testParseSetupLog(self):
    """Tests the Parse function on setup log."""
    parser = setupapi.SetupapiLogParser()
    storage_writer = self._ParseFile(['setupapi.setup.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 16)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-11-22 17:53:16.599000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-11-22 17:53:28.973000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2015-11-22 17:53:29.305000')

    expected_message = (
        'Description: Setup Plug and Play Device Install '
        '| Exit status: SUCCESS')
    expected_short_message = ('Setup Plug and Play Device Install')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[7]
    expected_message = (
        'Description: Setup online Device Install (Hardware initiated) - SW'
        '\\{97ebaacc-95bd-11d0-a3ea-00a0c9223196}'
        '\\{53172480-4791-11D0-A5D6-28DB04C10000} | Exit status: SUCCESS')
    expected_short_message = (
        'Setup online Device Install (Hardware initiated) - SW'
        '\\{97ebaacc-95bd-11d0-a3e...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[15]

    self.CheckTimestamp(event.timestamp, '2015-11-22 17:57:17.502000')

    expected_message = (
        'Description: Setup Import Driver Package - C:\\Windows\\system32'
        '\\spool\\tools\\Microsoft XPS Document Writer\\prnms001.Inf '
        '| Exit status: SUCCESS')
    expected_short_message = (
        'Setup Import Driver Package - C:\\Windows\\system32\\spool'
        '\\tools\\Microsoft XPS D...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
