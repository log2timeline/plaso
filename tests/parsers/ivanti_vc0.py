#!/usr/bin/env python3
"""Tests for the Ivanti Connect Secure (.vc0) log parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import ivanti_vc0

from tests.parsers import test_lib


class _TestFileEntry:
    """Test file entry."""

    def __init__(self, name):
        """Initializes a test file entry.

        Args:
          name (str): file entry name.
        """
        super().__init__()
        self.name = name


class IvantiVC0ParserTest(test_lib.ParserTestCase):
    """Tests for the Ivanti Connect Secure (.vc0) log parser."""

    def testFileEntryFilter(self):
        """Tests the file entry filter."""
        file_entry_filter = ivanti_vc0.VC0FileEntryFilter()

        for filename in (
            "log.access.vc0",
            "log.admin.vc0",
            "log.events.vc0",
            "log.events.vc0.old",
            "LOG.EVENTS.VC0",
        ):
            self.assertTrue(file_entry_filter.Match(_TestFileEntry(filename)))

        for filename in (
            "events.vc0",
            "log.vc0",
            "log.events.txt",
            "log.events.vc0.tmp",
            "random.bin",
        ):
            self.assertFalse(file_entry_filter.Match(_TestFileEntry(filename)))

        self.assertFalse(file_entry_filter.Match(None))

    def testParse(self):
        """Tests the Parse function."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.events.vc0"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        # invalid VC0 timestamp in record: !badtime.00000003
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "body": "User login succeeded",
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics.example.com",
            "ip_address": "203.0.113.10",
            "line_number": 1,
            "log_type": "events",
            "message_code": "SYS12345",
            "realm": "Root",
            "record_identifier": "65c4a64f.00000001",
            "recorded_time": "2024-02-08T10:00:47+00:00",
            "username": "jdoe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithUnsupportedFile(self):
        """Tests the Parse function with an unsupported file."""
        parser = ivanti_vc0.IvantiVC0Parser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("log.events.vc0", b"\x00" * 8192)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

    def testParseWithEmptyVC0File(self):
        """Tests the Parse function with an empty .vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = b"".join([b"\x05\x00\x00\x00\x01\x00\x00\x00", b"\x00" * 8184])
        file_object = self._CreateFileObject("log.events.vc0", data)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
