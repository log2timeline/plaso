#!/usr/bin/env python3
"""Tests for the Windows shell items parser."""

import unittest

import pyfwsi

from plaso.parsers.shared import shell_items

from tests.parsers import test_lib


class ShellItemsParserTest(test_lib.ParserTestCase):
    """Tests for the Windows shell items parser."""

    _TEST_DATA = bytes(
        bytearray(
            [
                0x14,
                0x00,
                0x1F,
                0x50,
                0xE0,
                0x4F,
                0xD0,
                0x20,
                0xEA,
                0x3A,
                0x69,
                0x10,
                0xA2,
                0xD8,
                0x08,
                0x00,
                0x2B,
                0x30,
                0x30,
                0x9D,
                0x19,
                0x00,
                0x2F,
                0x43,
                0x3A,
                0x5C,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x94,
                0x00,
                0x31,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x11,
                0x00,
                0x50,
                0x52,
                0x4F,
                0x47,
                0x52,
                0x41,
                0x7E,
                0x32,
                0x00,
                0x00,
                0x7C,
                0x00,
                0x08,
                0x00,
                0x04,
                0x00,
                0xEF,
                0xBE,
                0xEE,
                0x3A,
                0x85,
                0x1A,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x2A,
                0x00,
                0x00,
                0x00,
                0x12,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x52,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x50,
                0x00,
                0x72,
                0x00,
                0x6F,
                0x00,
                0x67,
                0x00,
                0x72,
                0x00,
                0x61,
                0x00,
                0x6D,
                0x00,
                0x20,
                0x00,
                0x46,
                0x00,
                0x69,
                0x00,
                0x6C,
                0x00,
                0x65,
                0x00,
                0x73,
                0x00,
                0x20,
                0x00,
                0x28,
                0x00,
                0x78,
                0x00,
                0x38,
                0x00,
                0x36,
                0x00,
                0x29,
                0x00,
                0x00,
                0x00,
                0x40,
                0x00,
                0x73,
                0x00,
                0x68,
                0x00,
                0x65,
                0x00,
                0x6C,
                0x00,
                0x6C,
                0x00,
                0x33,
                0x00,
                0x32,
                0x00,
                0x2E,
                0x00,
                0x64,
                0x00,
                0x6C,
                0x00,
                0x6C,
                0x00,
                0x2C,
                0x00,
                0x2D,
                0x00,
                0x32,
                0x00,
                0x31,
                0x00,
                0x38,
                0x00,
                0x31,
                0x00,
                0x37,
                0x00,
                0x00,
                0x00,
                0x18,
                0x00,
                0x4A,
                0x00,
                0x31,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x10,
                0x00,
                0x4E,
                0x65,
                0x72,
                0x6F,
                0x00,
                0x00,
                0x36,
                0x00,
                0x08,
                0x00,
                0x04,
                0x00,
                0xEF,
                0xBE,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x2A,
                0x00,
                0x00,
                0x00,
                0xCB,
                0x39,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4E,
                0x00,
                0x65,
                0x00,
                0x72,
                0x00,
                0x6F,
                0x00,
                0x00,
                0x00,
                0x14,
                0x00,
                0x50,
                0x00,
                0x31,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x10,
                0x00,
                0x4E,
                0x45,
                0x52,
                0x4F,
                0x39,
                0x7E,
                0x31,
                0x00,
                0x3A,
                0x00,
                0x08,
                0x00,
                0x04,
                0x00,
                0xEF,
                0xBE,
                0x3D,
                0x3C,
                0xAA,
                0xAB,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x2A,
                0x00,
                0x00,
                0x00,
                0xCC,
                0x39,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4E,
                0x00,
                0x65,
                0x00,
                0x72,
                0x00,
                0x6F,
                0x00,
                0x20,
                0x00,
                0x39,
                0x00,
                0x00,
                0x00,
                0x16,
                0x00,
                0x60,
                0x00,
                0x31,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x10,
                0x00,
                0x4E,
                0x45,
                0x52,
                0x4F,
                0x49,
                0x4E,
                0x7E,
                0x31,
                0x00,
                0x00,
                0x48,
                0x00,
                0x08,
                0x00,
                0x04,
                0x00,
                0xEF,
                0xBE,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x2A,
                0x00,
                0x00,
                0x00,
                0xC1,
                0x3D,
                0x01,
                0x00,
                0x00,
                0x00,
                0x02,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4E,
                0x00,
                0x65,
                0x00,
                0x72,
                0x00,
                0x6F,
                0x00,
                0x20,
                0x00,
                0x49,
                0x00,
                0x6E,
                0x00,
                0x66,
                0x00,
                0x6F,
                0x00,
                0x54,
                0x00,
                0x6F,
                0x00,
                0x6F,
                0x00,
                0x6C,
                0x00,
                0x00,
                0x00,
                0x18,
                0x00,
                0x62,
                0x00,
                0x32,
                0x00,
                0x18,
                0xBA,
                0x46,
                0x00,
                0xC5,
                0x3A,
                0xAA,
                0xA1,
                0x20,
                0x00,
                0x49,
                0x6E,
                0x66,
                0x6F,
                0x54,
                0x6F,
                0x6F,
                0x6C,
                0x2E,
                0x65,
                0x78,
                0x65,
                0x00,
                0x00,
                0x46,
                0x00,
                0x08,
                0x00,
                0x04,
                0x00,
                0xEF,
                0xBE,
                0xC5,
                0x3A,
                0xAA,
                0xA1,
                0x3D,
                0x3C,
                0xC6,
                0xAB,
                0x2A,
                0x00,
                0x00,
                0x00,
                0xC5,
                0x3D,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x49,
                0x00,
                0x6E,
                0x00,
                0x66,
                0x00,
                0x6F,
                0x00,
                0x54,
                0x00,
                0x6F,
                0x00,
                0x6F,
                0x00,
                0x6C,
                0x00,
                0x2E,
                0x00,
                0x65,
                0x00,
                0x78,
                0x00,
                0x65,
                0x00,
                0x00,
                0x00,
                0x1C,
                0x00,
                0x00,
                0x00,
            ]
        )
    )

    # TODO: add tests for CopyToPath
    # TODO: add tests for GetUpperPathSegment

    # pylint: disable=protected-access

    def _GetShellItems(self):
        """Retrieves the shell items of the test data.

        Returns:
          list[pyfwsi.item]: shell items.
        """
        shell_item_list = pyfwsi.item_list()
        shell_item_list.copy_from_byte_stream(self._TEST_DATA)
        return list(shell_item_list.items)

    def testGetDateTime(self):
        """Tests the _GetDateTime function."""
        parser = shell_items.ShellItemsParser("test_origin")

        date_time = parser._GetDateTime(0x00000000)
        self.assertIsNone(date_time)

        date_time = parser._GetDateTime(None)
        self.assertIsNone(date_time)

        date_time = parser._GetDateTime(0xABAA3C3D)
        self.assertIsNotNone(date_time)
        self.assertEqual(date_time.CopyToDateTimeString(), "2010-01-29 21:29:20")

    def testGetSanitizedPathString(self):
        """Tests the _GetSanitizedPathString function."""
        parser = shell_items.ShellItemsParser("test_origin")

        path_string = parser._GetSanitizedPathString(None)
        self.assertIsNone(path_string)

        path_string = parser._GetSanitizedPathString("")
        self.assertIsNone(path_string)

        path_string = parser._GetSanitizedPathString("InfoTool.exe")
        self.assertEqual(path_string, "InfoTool.exe")

        path_string = parser._GetSanitizedPathString("C:\\Nero\x01\x7f")
        self.assertEqual(path_string, "C:\\\\Nero\\x01\\x7f")

    def testParseShellItem(self):
        """Tests the _ParseShellItem function."""
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser = shell_items.ShellItemsParser("test_origin")

        root_folder, volume, file_entry = self._GetShellItems()[:3]

        # Shell items that are not a file entry only add a path segment.
        parser._ParseShellItem(parser_mediator, root_folder)
        parser._ParseShellItem(parser_mediator, volume)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)
        self.assertEqual(parser.CopyToPath(), "<My Computer> C:\\\\")

        parser._ParseShellItem(parser_mediator, file_entry)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        expected_event_values = {
            "access_time": "2010-01-29T21:29:20+00:00",
            "creation_time": "2009-07-14T03:20:10+00:00",
            "data_type": "windows:shell_item:file_entry",
            "file_reference": "274-1",
            "long_name": "Program Files (x86)",
            "modification_time": "2010-01-29T21:29:20+00:00",
            "name": "PROGRA~2",
            "origin": "test_origin",
            "shell_item_path": "<My Computer> C:\\\\Program Files (x86)",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseShellItemPathSegment(self):
        """Tests the _ParseShellItemPathSegment function."""
        parser = shell_items.ShellItemsParser("test_origin")

        path_segments = [
            parser._ParseShellItemPathSegment(shell_item)
            for shell_item in self._GetShellItems()
        ]
        self.assertEqual(
            path_segments,
            [
                "<My Computer>",
                "C:\\\\",
                "Program Files (x86)",
                "Nero",
                "Nero 9",
                "Nero InfoTool",
                "InfoTool.exe",
            ],
        )

        # Determining a path segment does not change the shell item path.
        self.assertIsNone(parser.CopyToPath())

    def testParseByteStream(self):
        """Tests the ParseByteStream function."""
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser = shell_items.ShellItemsParser("test_origin")
        parser.ParseByteStream(parser_mediator, self._TEST_DATA)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_shell_item_path = (
            "<My Computer> C:\\\\Program Files (x86)\\\\Nero\\\\Nero 9\\\\"
            "Nero InfoTool\\\\InfoTool.exe"
        )

        shell_item_path = parser.CopyToPath()
        self.assertEqual(shell_item_path, expected_shell_item_path)

        path_segment = parser.GetUpperPathSegment()
        self.assertEqual(path_segment, "InfoTool.exe")


if __name__ == "__main__":
    unittest.main()
