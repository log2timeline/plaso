#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Apple System Log file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import asl

from tests.parsers import test_lib


class ASLParserTest(test_lib.ParserTestCase):
  """Tests for Apple System Log file parser."""

  # pylint: disable=protected-access

  _TEST_RECORD = bytes(bytearray([
      0x00, 0x01, 0x00, 0x00, 0x00, 0x14, 0x44, 0x61, 0x72, 0x6b, 0x54, 0x65,
      0x6d, 0x70, 0x6c, 0x61, 0x72, 0x2d, 0x32, 0x2e, 0x6c, 0x6f, 0x63, 0x61,
      0x6c, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x0a, 0x6c, 0x6f, 0x63, 0x61,
      0x74, 0x69, 0x6f, 0x6e, 0x64, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x14,
      0x63, 0x6f, 0x6d, 0x2e, 0x61, 0x70, 0x70, 0x6c, 0x65, 0x2e, 0x6c, 0x6f,
      0x63, 0x61, 0x74, 0x69, 0x6f, 0x6e, 0x64, 0x00, 0x00, 0x01, 0x00, 0x00,
      0x00, 0x11, 0x43, 0x46, 0x4c, 0x6f, 0x67, 0x20, 0x4c, 0x6f, 0x63, 0x61,
      0x6c, 0x20, 0x54, 0x69, 0x6d, 0x65, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
      0x18, 0x32, 0x30, 0x31, 0x33, 0x2d, 0x31, 0x31, 0x2d, 0x32, 0x35, 0x20,
      0x30, 0x39, 0x3a, 0x34, 0x35, 0x3a, 0x33, 0x35, 0x2e, 0x37, 0x30, 0x31,
      0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x0d, 0x43, 0x46, 0x4c, 0x6f, 0x67,
      0x20, 0x54, 0x68, 0x72, 0x65, 0x61, 0x64, 0x00, 0x00, 0x01, 0x00, 0x00,
      0x00, 0x96, 0x49, 0x6e, 0x63, 0x6f, 0x72, 0x72, 0x65, 0x63, 0x74, 0x20,
      0x4e, 0x53, 0x53, 0x74, 0x72, 0x69, 0x6e, 0x67, 0x45, 0x6e, 0x63, 0x6f,
      0x64, 0x69, 0x6e, 0x67, 0x20, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x20, 0x30,
      0x78, 0x38, 0x30, 0x30, 0x30, 0x31, 0x30, 0x30, 0x20, 0x64, 0x65, 0x74,
      0x65, 0x63, 0x74, 0x65, 0x64, 0x2e, 0x20, 0x41, 0x73, 0x73, 0x75, 0x6d,
      0x69, 0x6e, 0x67, 0x20, 0x4e, 0x53, 0x41, 0x53, 0x43, 0x49, 0x49, 0x53,
      0x74, 0x72, 0x69, 0x6e, 0x67, 0x45, 0x6e, 0x63, 0x6f, 0x64, 0x69, 0x6e,
      0x67, 0x2e, 0x20, 0x57, 0x69, 0x6c, 0x6c, 0x20, 0x73, 0x74, 0x6f, 0x70,
      0x20, 0x74, 0x68, 0x69, 0x73, 0x20, 0x63, 0x6f, 0x6d, 0x70, 0x61, 0x74,
      0x69, 0x62, 0x6c, 0x69, 0x74, 0x79, 0x20, 0x6d, 0x61, 0x70, 0x70, 0x69,
      0x6e, 0x67, 0x20, 0x62, 0x65, 0x68, 0x61, 0x76, 0x69, 0x6f, 0x72, 0x20,
      0x69, 0x6e, 0x20, 0x74, 0x68, 0x65, 0x20, 0x6e, 0x65, 0x61, 0x72, 0x20,
      0x66, 0x75, 0x74, 0x75, 0x72, 0x65, 0x2e, 0x00, 0x00, 0x01, 0x00, 0x00,
      0x00, 0x11, 0x53, 0x65, 0x6e, 0x64, 0x65, 0x72, 0x5f, 0x4d, 0x61, 0x63,
      0x68, 0x5f, 0x55, 0x55, 0x49, 0x44, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
      0x25, 0x35, 0x30, 0x45, 0x31, 0x46, 0x37, 0x36, 0x41, 0x2d, 0x36, 0x30,
      0x46, 0x46, 0x2d, 0x33, 0x36, 0x38, 0x43, 0x2d, 0x42, 0x37, 0x34, 0x45,
      0x2d, 0x45, 0x42, 0x34, 0x38, 0x46, 0x36, 0x44, 0x39, 0x38, 0x43, 0x35,
      0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa4, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x03, 0xce, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x8c, 0x1e,
      0x00, 0x00, 0x00, 0x00, 0x52, 0x93, 0x1c, 0x3f, 0x2a, 0x0c, 0xc9, 0x28,
      0x00, 0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x45, 0x00, 0x00, 0x00, 0xcd,
      0x00, 0x00, 0x00, 0xcd, 0x00, 0x00, 0x00, 0xcd, 0xff, 0xff, 0xff, 0xff,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1a,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2a, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x8c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5b,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79, 0x84, 0x31, 0x30, 0x30,
      0x37, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x28,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x3f, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00]))

  def testParseRecord(self):
    """Tests the _ParseRecord function."""
    parser = asl.ASLParser()

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    file_object = self._CreateFileObject('asl', self._TEST_RECORD)

    next_record_offset = parser._ParseRecord(parser_mediator, file_object, 362)
    self.assertEqual(next_record_offset, 974)

    # Test with log entry descriptor data too small.
    file_object = self._CreateFileObject('asl', self._TEST_RECORD[:452])

    with self.assertRaises(errors.ParseError):
      parser._ParseRecord(parser_mediator, file_object, 362)

    # TODO: test with invalid additional data size.

  def testParseRecordExtraField(self):
    """Tests the _ParseRecordExtraField function."""
    parser = asl.ASLParser()
    extra_field_map = parser._GetDataTypeMap('asl_record_extra_field')

    extra_field = extra_field_map.CreateStructureValues(
        name_string_offset=10, value_string_offset=20)
    extra_field_data = extra_field_map.FoldByteStream(extra_field)

    extra_field_value = parser._ParseRecordExtraField(extra_field_data, 0)
    self.assertEqual(extra_field_value.name_string_offset, 10)
    self.assertEqual(extra_field_value.value_string_offset, 20)

    # Test with extra field data too small.
    with self.assertRaises(errors.ParseError):
      parser._ParseRecordExtraField(extra_field_data[:-1], 0)

  def testParseRecordString(self):
    """Tests the _ParseRecordString function."""
    parser = asl.ASLParser()
    string_map = parser._GetDataTypeMap('asl_record_string')

    string = string_map.CreateStructureValues(
        unknown1=0, string_size=4, string='test')
    string_data = string_map.FoldByteStream(string)
    # Prefix the string data with 4 bytes since string offset cannot be 0.
    string_data = b''.join([b'\x00\x00\x00\x00', string_data])

    file_object = self._CreateFileObject('asl', string_data)
    string_value = parser._ParseRecordString(file_object, 0)
    self.assertIsNone(string_value)

    file_object = self._CreateFileObject('asl', string_data)
    string_value = parser._ParseRecordString(file_object, 4)
    self.assertEqual(string_value, 'test')

    # Test with string data too small.
    file_object = self._CreateFileObject('asl', string_data[:-1])
    with self.assertRaises(errors.ParseError):
      parser._ParseRecordString(file_object, 4)

    # Test with inline string data.
    file_object = self._CreateFileObject('asl', b'')
    string_value = parser._ParseRecordString(file_object, 0x8474657374000000)
    self.assertEqual(string_value, 'test')

    file_object = self._CreateFileObject('asl', b'')
    with self.assertRaises(errors.ParseError):
      parser._ParseRecordString(file_object, 0xf474657374000000)

    file_object = self._CreateFileObject('asl', b'')
    with self.assertRaises(errors.ParseError):
      parser._ParseRecordString(file_object, 0x8f74657374000000)

    file_object = self._CreateFileObject('asl', b'')
    with self.assertRaises(errors.ParseError):
      parser._ParseRecordString(file_object, 0x84ffffffff000000)

  def testGetFormatSpecification(self):
    """Tests the GetFormatSpecification function."""
    format_specification = asl.ASLParser.GetFormatSpecification()
    self.assertIsNotNone(format_specification)

  def _CreateFileHeaderData(self, parser):
    """Creates file header test data.

    Args:
      parser (ASLParser): ASL parser.

    Returns:
      bytes: file header test data.
    """
    file_header_map = parser._GetDataTypeMap('asl_file_header')

    unknown1_data = b'\x00' * 36
    file_header = file_header_map.CreateStructureValues(
        signature=b'ASL DB\x00\x00\x00\x00\x00\x00', format_version=2,
        first_log_entry_offset=80, creation_time=0, cache_size=0,
        last_log_entry_offset=0, unknown1=unknown1_data)
    return file_header_map.FoldByteStream(file_header)

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = asl.ASLParser()

    file_header_data = self._CreateFileHeaderData(parser)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    file_object = self._CreateFileObject('asl', file_header_data)

    parser.ParseFileObject(parser_mediator, file_object)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test with file header data too small.
    file_object = self._CreateFileObject('asl', file_header_data[:-1])

    with self.assertRaises(errors.WrongParser):
      parser.ParseFileObject(parser_mediator, file_object)

    # Test with invalid signature.
    file_object = self._CreateFileObject(
        'asl', b''.join([b'\xff\xff\xff\xff', file_header_data[4:]]))

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    with self.assertRaises(errors.WrongParser):
      parser.ParseFileObject(parser_mediator, file_object)

    # Test with first record data too small.
    file_object = self._CreateFileObject('asl', b''.join([
        file_header_data, self._TEST_RECORD[:452]]))

    parser.ParseFileObject(parser_mediator, file_object)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParse(self):
    """Tests the Parse function."""
    parser = asl.ASLParser()
    storage_writer = self._ParseFile(['applesystemlog.asl'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2013-11-25T09:45:35+00:00',
        'data_type': 'macos:asl:file',
        'format_version': 2,
        'is_dirty': False}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Note that "compatiblity" is spelt incorrectly in the actual message being
    # tested here.
    expected_event_values = {
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'macos:asl:entry',
        'extra_information': (
            'CFLog Local Time: 2013-11-25 09:45:35.701, '
            'CFLog Thread: 1007, '
            'Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51'),
        'facility': 'com.apple.locationd',
        'group_identifier': 205,
        'level': 4,
        'message': (
            'Incorrect NSStringEncoding value 0x8000100 detected. '
            'Assuming NSASCIIStringEncoding. Will stop this compatiblity '
            'mapping behavior in the near future.'),
        'message_identifier': 101406,
        'process_identifier': 69,
        'read_group_identifier': -1,
        'read_user_identifier': 205,
        'record_position': 442,
        'sender': 'locationd',
        'user_identifier': 205,
        'written_time': '2013-11-25T09:45:35.705481000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check a second event data to ensure record strings are parsed correctly.
    expected_event_values = {
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'macos:asl:entry',
        'extra_information': (
            'CFLog Local Time: 2013-11-25 17:12:43.537, '
            'CFLog Thread: 1007, '
            'Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51'),
        'facility': 'com.apple.locationd',
        'group_identifier': 205,
        'level': 4,
        'message': (
            'Incorrect NSStringEncoding value 0x8000100 detected. '
            'Assuming NSASCIIStringEncoding. Will stop this compatiblity '
            'mapping behavior in the near future.'),
        'message_identifier': 102643,
        'process_identifier': 69,
        'read_group_identifier': -1,
        'read_user_identifier': 205,
        'record_position': 974,
        'sender': 'locationd',
        'user_identifier': 205,
        'written_time': '2013-11-25T17:12:43.571140000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testParseDirtyFile(self):
    """Tests the Parse function on a dirty file."""
    parser = asl.ASLParser()
    storage_writer = self._ParseFile(['2019.09.26.asl'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 319)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 1)

    expected_event_values = {
        'creation_time': '2019-09-25T22:50:16+00:00',
        'data_type': 'macos:asl:file',
        'format_version': 2,
        'is_dirty': True}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 318)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
