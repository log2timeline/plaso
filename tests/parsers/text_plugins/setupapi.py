#!/usr/bin/env python3
"""Tests for the Windows SetupAPI log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import setupapi

from tests.parsers.text_plugins import test_lib


class SetupAPILogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Windows SetupAPI log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = setupapi.SetupAPILogTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'[Device Install Log]\n'
        b'     OS Version = 10.0.10240\n'
        b'     Service Pack = 0.0\n'
        b'     Suite = 0x0100\n'
        b'     ProductType = 1\n'
        b'     Architecture = amd64\n'
        b'\n'
        b'[BeginLog]\n'
        b'\n'
        b'[Boot Session: 2015/11/22 17:58:03.498]\n'
        b'\n'
        b'>>>  [Device Install (Hardware initiated) - '
        b'SWD\\IP_TUNNEL_VBUS\\ISATAP_0]\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcessWithDevLog(self):
    """Tests the Process function with setupapi.dev.log."""
    plugin = setupapi.SetupAPILogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['setupapi.dev.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 194)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'end_time': '2016-10-12T03:36:30.998',
        'entry_type': (
            'Device Install (DiInstallDriver) - C:\\Windows\\System32'
            '\\DriverStore\\FileRepository\\prnms003.inf_x86_8f17aac186c70ea6'
            '\\prnms003.inf'),
        'exit_status': 'SUCCESS',
        'start_time': '2016-10-12T03:36:30.936'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 28)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithSetupLog(self):
    """Tests the Process function with setupapi.setup.log."""
    plugin = setupapi.SetupAPILogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['setupapi.setup.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 16)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'setupapi:log:line',
        'end_time': '2015-11-22T17:57:17.704',
        'entry_type': (
            'Setup Import Driver Package - C:\\Windows\\system32'
            '\\spool\\tools\\Microsoft XPS Document Writer\\prnms001.Inf'),
        'start_time': '2015-11-22T17:57:17.502'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 15)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
