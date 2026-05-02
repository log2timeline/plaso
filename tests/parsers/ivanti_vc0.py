#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Ivanti Connect Secure .vc0 log parser."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import ivanti_vc0

from tests.parsers import test_lib


class IvantiVC0ParserTest(test_lib.ParserTestCase):
  """Tests for the Ivanti Connect Secure .vc0 log parser."""

  def _ParseData(self, data):
    """Parses .vc0 data.

    Args:
      data (bytes): .vc0 data.

    Returns:
      FakeStorageWriter: storage writer.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/log.events.vc0', data)

    file_entry = file_system_builder.file_system.GetFileEntryByPath(
        '/log.events.vc0')

    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)
    parser_mediator.SetFileEntry(file_entry)

    event_data_stream = events.EventDataStream()
    event_data_stream.path_spec = file_entry.path_spec
    parser_mediator.ProduceEventDataStream(event_data_stream)

    parser = ivanti_vc0.IvantiVC0Parser()
    file_object = file_entry.GetFileObject()
    parser.Parse(parser_mediator, file_object)

    return storage_writer

  def testParse(self):
    """Tests the Parse function."""
    data = b''.join([
        b'\x05\x00\x00\x00\x01\x00\x00\x00',
        b'\x00' * 8184,
        b'\x05',
        b'65c4a64f.00000001\tics.example.com\tSYS12345\tvc0\tRoot\t',
        b'203.0.113.10\tjdoe\tUser login succeeded\n',
        b'66618fe1.00000002\tics.example.com\tADM54321\tvc0\tRoot\t',
        b'203.0.113.20\tadmin\tConfiguration changed',
        b'\x05',
        b'!badtime.00000003\tics.example.com\tSYS12345\tvc0\tRoot\t',
        b'203.0.113.55\tbaduser\tInvalid timestamp\n'])

    storage_writer = self._ParseData(data)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'User login succeeded',
        'data_type': 'ivanti:connect_secure:vc0:record',
        'hostname': 'ics.example.com',
        'ip_address': '203.0.113.10',
        'line_identifier': '00000001',
        'log_file_type': 'events',
        'message_code': 'SYS12345',
        'realm': 'Root',
        'record_identifier': '65c4a64f.00000001',
        'record_values': '203.0.113.10\tjdoe\tUser login succeeded',
        'recorded_time': '2024-02-08T10:00:47+00:00',
        'source_filename': 'log.events.vc0',
        'username': 'jdoe'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': 'Configuration changed',
        'hostname': 'ics.example.com',
        'ip_address': '203.0.113.20',
        'line_identifier': '00000002',
        'message_code': 'ADM54321',
        'recorded_time': '2024-06-06T10:30:57+00:00',
        'username': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithUnsupportedFile(self):
    """Tests the Parse function with an unsupported file."""
    file_object = self._CreateFileObject('log.events.vc0', b'\x00' * 8192)
    parser_mediator = self._CreateParserMediator(self._CreateStorageWriter())

    parser = ivanti_vc0.IvantiVC0Parser()
    with self.assertRaises(errors.WrongParser):
      parser.Parse(parser_mediator, file_object)

  def testParseWithEmptyVC0File(self):
    """Tests the Parse function with an empty .vc0 file."""
    data = b''.join([
        b'\x05\x00\x00\x00\x01\x00\x00\x00',
        b'\x00' * 8184])

    storage_writer = self._ParseData(data)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
