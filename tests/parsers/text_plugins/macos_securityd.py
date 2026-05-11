#!/usr/bin/env python3
"""Tests the MacOS security daemon (securityd) log file text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import macos_securityd

from tests.parsers.text_plugins import test_lib


class MacOSSecuritydLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests the MacOS security daemon (securityd) log file text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = macos_securityd.MacOSSecuritydLogTextPlugin()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Feb 26 19:11:56 secd[1] <Error> [user{} ]: '
        b'securityd_xpc_dictionary_handler\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_securityd.MacOSSecuritydLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['security.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '0000-02-26T19:11:56+00:00',
        'caller': None,
        'data_type': 'macos:securityd_log:entry',
        'facility': 'user',
        'level': 'Error',
        'message': (
            'securityd_xpc_dictionary_handler EscrowSecurityAl'
            '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
            'l\xedka, setja \xedslensku inn.'),
        'security_api': None,
        'sender_pid': 1,
        'sender': 'secd'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check repeated line.
    expected_event_values = {
        'added_time': '0001-12-24T01:21:47+00:00',
        'caller': None,
        'data_type': 'macos:securityd_log:entry',
        'facility': 'user',
        'level': 'Error',
        'message': 'Repeated 3 times: Happy new year!',
        'security_api': None,
        'sender_pid': 456,
        'sender': 'secd'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
