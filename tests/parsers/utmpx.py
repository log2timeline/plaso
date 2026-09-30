#!/usr/bin/env python3
"""Tests for UTMPX file parser."""

import unittest

from plaso.parsers import utmpx

from tests.parsers import test_lib


class UtmpxParserTest(test_lib.ParserTestCase):
    """Tests for utmpx file parser."""

    def testParse(self):
        """Tests the Parse function."""
        parser = utmpx.UtmpxParser()
        storage_writer = self._ParseFile(["utmpx_mac"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "macos:utmpx:entry",
            "hostname": "localhost",
            "login_type": 7,
            "pid": 67,
            "terminal": "console",
            "terminal_identifier": 65583,
            "username": "moxilo",
            "written_time": "2013-11-13T17:52:41.736713+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testParseFileObjectWithUnsupportedLoginType(self):
        """Tests the ParseFileObject function with an unsupported login type."""
        parser = utmpx.UtmpxParser()

        test_file_path = self._GetTestFilePath(["utmpx_mac"])
        with open(test_file_path, "rb") as file_object:
            file_data = bytearray(file_object.read())

        # Set the login type of the second entry, at offset 2 * 628 + 296, to 99.
        file_data[1552:1554] = b"\x63\x00"

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("utmpx_mac", bytes(file_data))

        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        offsets = [
            event_data.offset
            for event_data in storage_writer.GetAttributeContainers("event_data")
        ]
        self.assertEqual(offsets, [628, 1884, 2512, 3140, 3768])

    def testParseFileObjectWithTruncatedEntry(self):
        """Tests the ParseFileObject function with a truncated last entry."""
        parser = utmpx.UtmpxParser()

        test_file_path = self._GetTestFilePath(["utmpx_mac"])
        with open(test_file_path, "rb") as file_object:
            file_data = file_object.read()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("utmpx_mac", file_data[:-100])

        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        offsets = [
            event_data.offset
            for event_data in storage_writer.GetAttributeContainers("event_data")
        ]
        self.assertEqual(offsets, [628, 1256, 1884, 2512, 3140])


if __name__ == "__main__":
    unittest.main()
