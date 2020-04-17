#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parser test for MacOS Cups IPP Log files."""

from __future__ import unicode_literals

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import cups_ipp

from tests.parsers import test_lib


class CupsIppParserTest(test_lib.ParserTestCase):
  """Tests for MacOS Cups IPP parser."""

  # pylint: disable=protected-access

  _ATTRIBUTES_GROUP_DATA = bytes(bytearray([
      0x01, 0x47, 0x00, 0x12, 0x61, 0x74, 0x74, 0x72, 0x69, 0x62, 0x75, 0x74,
      0x65, 0x73, 0x2d, 0x63, 0x68, 0x61, 0x72, 0x73, 0x65, 0x74, 0x00, 0x05,
      0x75, 0x74, 0x66, 0x2d, 0x38, 0x03]))

  def _CreateAttributeTestData(self, parser, tag_value, name, value_data):
    """Creates attribute test data.

    Args:
      parser (CupsIppParser): CUPS IPP parser.
      tag_value (int): value of the attribute tag.
      name (str): name of the attribute.
      value_data (bytes): data of the attribute value.

    Returns:
      bytes: attribute test data.
    """
    attribute_map = parser._GetDataTypeMap('cups_ipp_attribute')

    attribute = attribute_map.CreateStructureValues(
        tag_value=tag_value, name_size=len(name), name=name,
        value_data_size=len(value_data), value_data=value_data)
    return attribute_map.FoldByteStream(attribute)

  def _CreateDateTimeValueData(self, parser):
    """Creates date time value test data.

    Args:
      parser (CupsIppParser): CUPS IPP parser.

    Returns:
      bytes: date time value test data.
    """
    datetime_map = parser._GetDataTypeMap('cups_ipp_datetime_value')

    datetime = datetime_map.CreateStructureValues(
        year=2018, month=11, day_of_month=27, hours=16, minutes=41, seconds=51,
        deciseconds=5, direction_from_utc=ord('+'), hours_from_utc=1,
        minutes_from_utc=0)
    return datetime_map.FoldByteStream(datetime)

  def _CreateHeaderData(self, parser):
    """Creates header test data.

    Args:
      parser (CupsIppParser): CUPS IPP parser.

    Returns:
      bytes: header test data.
    """
    header_map = parser._GetDataTypeMap('cups_ipp_header')

    header = header_map.CreateStructureValues(
        major_version=1, minor_version=1, operation_identifier=5,
        request_identifier=0)
    return header_map.FoldByteStream(header)

  def testGetStringValue(self):
    """Tests the _GetStringValue function."""
    parser = cups_ipp.CupsIppParser()

    string_value = parser._GetStringValue({}, 'test')
    self.assertIsNone(string_value)

    string_value = parser._GetStringValue({'test': ['1', '2,3', '4']}, 'test')
    self.assertEqual(string_value, '1, "2,3", 4')

  def testParseAttribute(self):
    """Tests the _ParseAttribute function."""
    parser = cups_ipp.CupsIppParser()

    attribute_data = self._CreateAttributeTestData(
        parser, 0x00, 'test', b'\x12')
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'test')
    self.assertEqual(value, b'\x12')

    # Test with attribute data too small.
    file_object = self._CreateFileObject('cups_ipp', attribute_data[:-1])

    with self.assertRaises(errors.ParseError):
      parser._ParseAttribute(file_object)

    # Test attribute with integer value.
    attribute_data = self._CreateAttributeTestData(
        parser, 0x21, 'int', b'\x12\x34\x56\x78')
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'int')
    self.assertEqual(value, 0x12345678)

    # Test attribute with boolean value.
    attribute_data = self._CreateAttributeTestData(
        parser, 0x22, 'bool', b'\x01')
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'bool')
    self.assertEqual(value, True)

    # Test attribute with date time value.
    datetime_data = self._CreateDateTimeValueData(parser)
    attribute_data = self._CreateAttributeTestData(
        parser, 0x31, 'datetime', datetime_data)
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'datetime')
    self.assertIsNotNone(value)
    self.assertEqual(value.year, 2018)

    # Test attribute with string without language.
    attribute_data = self._CreateAttributeTestData(
        parser, 0x42, 'string', b'NOLANG')
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'string')
    self.assertEqual(value, 'NOLANG')

    # Test attribute with ASCII string and tag value charset.
    attribute_data = self._CreateAttributeTestData(
        parser, 0x47, 'charset', b'utf8')
    file_object = self._CreateFileObject('cups_ipp', attribute_data)

    name, value = parser._ParseAttribute(file_object)
    self.assertEqual(name, 'charset')
    self.assertEqual(value, 'utf8')

  def testParseAttributesGroup(self):
    """Tests the _ParseAttributesGroup function."""
    parser = cups_ipp.CupsIppParser()

    file_object = self._CreateFileObject(
        'cups_ipp', self._ATTRIBUTES_GROUP_DATA)

    name_value_pairs = list(parser._ParseAttributesGroup(file_object))
    self.assertEqual(name_value_pairs, [('attributes-charset', 'utf-8')])

    # Test with unsupported attributes groups start tag value.
    file_object = self._CreateFileObject('cups_ipp', b''.join([
        b'\xff', self._ATTRIBUTES_GROUP_DATA[1:]]))

    with self.assertRaises(errors.ParseError):
      list(parser._ParseAttributesGroup(file_object))

  def testParseBooleanValue(self):
    """Tests the _ParseBooleanValue function."""
    parser = cups_ipp.CupsIppParser()

    boolean_value = parser._ParseBooleanValue(b'\x00')
    self.assertFalse(boolean_value)

    boolean_value = parser._ParseBooleanValue(b'\x01')
    self.assertTrue(boolean_value)

    # Test with unsupported data.
    with self.assertRaises(errors.ParseError):
      parser._ParseBooleanValue(b'\x02')

  def testParseDateTimeValue(self):
    """Tests the _ParseDateTimeValue function."""
    parser = cups_ipp.CupsIppParser()

    datetime_data = self._CreateDateTimeValueData(parser)

    datetime_value = parser._ParseDateTimeValue(datetime_data, 0)
    self.assertIsNotNone(datetime_value)
    self.assertEqual(datetime_value.year, 2018)

    # Test with data too small.
    with self.assertRaises(errors.ParseError):
      parser._ParseDateTimeValue(datetime_data[:-1], 0)

  def testParseIntegerValue(self):
    """Tests the _ParseIntegerValue function."""
    parser = cups_ipp.CupsIppParser()

    integer_value = parser._ParseIntegerValue(b'\x00\x00\x00\x01', 0)
    self.assertEqual(integer_value, 1)

    # Test with data too small.
    with self.assertRaises(errors.ParseError):
      parser._ParseIntegerValue(b'\x01\x00\x00', 0)

  def testParseHeader(self):
    """Tests the _ParseHeader function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/cups_ipp', b'')

    test_path_spec = fake_path_spec.FakePathSpec(location='/cups_ipp')
    test_file_entry = file_system_builder.file_system.GetFileEntryByPathSpec(
        test_path_spec)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=test_file_entry)

    parser = cups_ipp.CupsIppParser()

    header_data = self._CreateHeaderData(parser)
    file_object = self._CreateFileObject('cups_ipp', header_data)

    parser._ParseHeader(parser_mediator, file_object)

    # Test with header data too small.
    file_object = self._CreateFileObject('cups_ipp', header_data[:-1])

    with self.assertRaises(errors.UnableToParseFile):
      parser._ParseHeader(parser_mediator, file_object)

    # Test with unsupported format version.
    header_map = parser._GetDataTypeMap('cups_ipp_header')

    header = header_map.CreateStructureValues(
        major_version=99, minor_version=1, operation_identifier=5,
        request_identifier=0)
    header_data = header_map.FoldByteStream(header)
    file_object = self._CreateFileObject('cups_ipp', header_data)

    with self.assertRaises(errors.UnableToParseFile):
      parser._ParseHeader(parser_mediator, file_object)

    # Test with unsupported operation identifier.
    header = header_map.CreateStructureValues(
        major_version=1, minor_version=1, operation_identifier=99,
        request_identifier=0)
    header_data = header_map.FoldByteStream(header)
    file_object = self._CreateFileObject('cups_ipp', header_data)

    parser._ParseHeader(parser_mediator, file_object)

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = cups_ipp.CupsIppParser()

    header_data = self._CreateHeaderData(parser)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    file_object = self._CreateFileObject('cups_ipp', b''.join([
        header_data, self._ATTRIBUTES_GROUP_DATA]))

    parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 0)

    # Test with attribute group data too small.
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    file_object = self._CreateFileObject('cups_ipp', b''.join([
        header_data, self._ATTRIBUTES_GROUP_DATA[:-1]]))

    parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 0)

    # Test attribute with date time value.
    datetime_data = self._CreateDateTimeValueData(parser)
    attribute_data = self._CreateAttributeTestData(
        parser, 0x31, 'date-time-at-creation', datetime_data)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    file_object = self._CreateFileObject('cups_ipp', b''.join([
        header_data, b'\x01', attribute_data, b'\x03']))

    parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

  def testParse(self):
    """Tests the Parse function."""
    # TODO: only tested against MacOS Cups IPP (Version 2.0)
    parser = cups_ipp.CupsIppParser()
    storage_writer = self._ParseFile(['mac_cups_ipp'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:21.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.application, 'LibreOffice')
    self.assertEqual(event_data.job_name, 'Assignament 1')
    self.assertEqual(event_data.computer_name, 'localhost')
    self.assertEqual(event_data.copies, 1)
    self.assertEqual(event_data.doc_type, 'application/pdf')
    self.assertEqual(
        event_data.job_id, 'urn:uuid:d51116d9-143c-3863-62aa-6ef0202de49a')
    self.assertEqual(event_data.owner, 'Joaquin Moreno Garijo')
    self.assertEqual(event_data.user, 'moxilo')
    self.assertEqual(event_data.printer_id, 'RHULBW')
    self.assertEqual(event_data.uri, 'ipp://localhost:631/printers/RHULBW')

    expected_message = (
        'User: moxilo '
        'Owner: Joaquin Moreno Garijo '
        'Job Name: Assignament 1 '
        'Application: LibreOffice '
        'Printer: RHULBW')
    expected_short_message = 'Job Name: Assignament 1'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:21.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_START)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:32.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_END)


if __name__ == '__main__':
  unittest.main()
