#!/usr/bin/env python3
"""Tests for Apple System Log file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import asl

from tests.parsers import test_lib


class ASLParserTest(test_lib.ParserTestCase):
    """Tests for Apple System Log file parser."""

    # pylint: disable=protected-access

    _TEST_RECORD = bytes.fromhex(
        "0001000000144461726b54656d706c61722d322e6c6f63616c0000010000000a6c6f63617469"
        "6f6e6400000100000014636f6d2e6170706c652e6c6f636174696f6e64000001000000114346"
        "4c6f67204c6f63616c2054696d6500000100000018323031332d31312d32352030393a34353a"
        "33352e3730310000010000000d43464c6f672054687265616400000100000096496e636f7272"
        "656374204e53537472696e67456e636f64696e672076616c7565203078383030303130302064"
        "657465637465642e20417373756d696e67204e534153434949537472696e67456e636f64696e"
        "672e2057696c6c2073746f70207468697320636f6d70617469626c697479206d617070696e67"
        "206265686176696f7220696e20746865206e656172206675747572652e000001000000115365"
        "6e6465725f4d6163685f555549440000010000002535304531463736412d363046462d333638"
        "432d423734452d454234384636443938433531000000000000a400000000000003ce00000000"
        "00018c1e0000000052931c3f2a0cc9280004000100000045000000cd000000cd000000cdffff"
        "ffff00000000000000060000000000000000000000000000001a000000000000002a00000000"
        "0000008c000000000000000000000000000000000000000000000044000000000000005b0000"
        "00000000007984313030370000000000000000000128000000000000013f0000000000000000"
    )

    def testParseRecord(self):
        """Tests the _ParseRecord function."""
        parser = asl.ASLParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("asl", self._TEST_RECORD)

        next_record_offset = parser._ParseRecord(parser_mediator, file_object, 362)
        self.assertEqual(next_record_offset, 974)

        # Test with log entry descriptor data too small.
        file_object = self._CreateFileObject("asl", self._TEST_RECORD[:452])

        with self.assertRaises(errors.ParseError):
            parser._ParseRecord(parser_mediator, file_object, 362)

        # TODO: test with invalid additional data size.

    def testParseRecordExtraField(self):
        """Tests the _ParseRecordExtraField function."""
        parser = asl.ASLParser()
        extra_field_map = parser._GetDataTypeMap("asl_record_extra_field")

        extra_field = extra_field_map.CreateStructureValues(
            name_string_offset=10, value_string_offset=20
        )
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
        string_map = parser._GetDataTypeMap("asl_record_string")

        string = string_map.CreateStructureValues(
            unknown1=0, string_size=4, string="test"
        )
        string_data = string_map.FoldByteStream(string)
        # Prefix the string data with 4 bytes since string offset cannot be 0.
        string_data = b"".join([b"\x00\x00\x00\x00", string_data])

        file_object = self._CreateFileObject("asl", string_data)
        string_value = parser._ParseRecordString(file_object, 0)
        self.assertIsNone(string_value)

        file_object = self._CreateFileObject("asl", string_data)
        string_value = parser._ParseRecordString(file_object, 4)
        self.assertEqual(string_value, "test")

        # Test with string data too small.
        file_object = self._CreateFileObject("asl", string_data[:-1])
        with self.assertRaises(errors.ParseError):
            parser._ParseRecordString(file_object, 4)

        # Test with inline string data.
        file_object = self._CreateFileObject("asl", b"")
        string_value = parser._ParseRecordString(file_object, 0x8474657374000000)
        self.assertEqual(string_value, "test")

        file_object = self._CreateFileObject("asl", b"")
        with self.assertRaises(errors.ParseError):
            parser._ParseRecordString(file_object, 0xF474657374000000)

        file_object = self._CreateFileObject("asl", b"")
        with self.assertRaises(errors.ParseError):
            parser._ParseRecordString(file_object, 0x8F74657374000000)

        file_object = self._CreateFileObject("asl", b"")
        with self.assertRaises(errors.ParseError):
            parser._ParseRecordString(file_object, 0x84FFFFFFFF000000)

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
        file_header_map = parser._GetDataTypeMap("asl_file_header")

        unknown1_data = b"\x00" * 36
        file_header = file_header_map.CreateStructureValues(
            signature=b"ASL DB\x00\x00\x00\x00\x00\x00",
            format_version=2,
            first_log_entry_offset=80,
            creation_time=0,
            cache_size=0,
            last_log_entry_offset=0,
            unknown1=unknown1_data,
        )
        return file_header_map.FoldByteStream(file_header)

    def testParseFileObject(self):
        """Tests the ParseFileObject function."""
        parser = asl.ASLParser()

        file_header_data = self._CreateFileHeaderData(parser)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("asl", file_header_data)

        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test with file header data too small.
        file_object = self._CreateFileObject("asl", file_header_data[:-1])

        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)

        # Test with invalid signature.
        file_object = self._CreateFileObject(
            "asl", b"".join([b"\xff\xff\xff\xff", file_header_data[4:]])
        )
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)

        # Test with first record data too small.
        file_object = self._CreateFileObject(
            "asl", b"".join([file_header_data, self._TEST_RECORD[:452]])
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParse(self):
        """Tests the Parse function."""
        parser = asl.ASLParser()
        storage_writer = self._ParseFile(["applesystemlog.asl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "creation_time": "2013-11-25T09:45:35+00:00",
            "data_type": "macos:asl:file",
            "format_version": 2,
            "is_dirty": False,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # Note that "compatiblity" is spelt incorrectly in the actual message being
        # tested here.
        expected_event_values = {
            "data_type": "macos:asl:entry",
            "extra_information": (
                "CFLog Local Time: 2013-11-25 09:45:35.701, "
                "CFLog Thread: 1007, "
                "Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51"
            ),
            "facility": "com.apple.locationd",
            "group_identifier": 205,
            "hostname": "DarkTemplar-2.local",
            "level": 4,
            "message_body": (
                "Incorrect NSStringEncoding value 0x8000100 detected. "
                "Assuming NSASCIIStringEncoding. Will stop this compatiblity "
                "mapping behavior in the near future."
            ),
            "message_identifier": 101406,
            "process_identifier": 69,
            "read_group_identifier": -1,
            "read_user_identifier": 205,
            "record_position": 442,
            "sender": "locationd",
            "user_identifier": 205,
            "written_time": "2013-11-25T09:45:35.705481000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Check a second event data to ensure record strings are parsed correctly.
        expected_event_values = {
            "data_type": "macos:asl:entry",
            "extra_information": (
                "CFLog Local Time: 2013-11-25 17:12:43.537, "
                "CFLog Thread: 1007, "
                "Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51"
            ),
            "facility": "com.apple.locationd",
            "group_identifier": 205,
            "hostname": "DarkTemplar-2.local",
            "level": 4,
            "message_body": (
                "Incorrect NSStringEncoding value 0x8000100 detected. "
                "Assuming NSASCIIStringEncoding. Will stop this compatiblity "
                "mapping behavior in the near future."
            ),
            "message_identifier": 102643,
            "process_identifier": 69,
            "read_group_identifier": -1,
            "read_user_identifier": 205,
            "record_position": 974,
            "sender": "locationd",
            "user_identifier": 205,
            "written_time": "2013-11-25T17:12:43.571140000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testParseDirtyFile(self):
        """Tests the Parse function on a dirty file."""
        parser = asl.ASLParser()
        storage_writer = self._ParseFile(["2019.09.26.asl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 319)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "creation_time": "2019-09-25T22:50:16+00:00",
            "data_type": "macos:asl:file",
            "format_version": 2,
            "is_dirty": True,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 318)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
