#!/usr/bin/env python3
"""Tests for the Windows Shortcut (LNK) parser."""

import unittest

from plaso.parsers import winlnk

from tests.parsers import test_lib


class WinLnkParserTest(test_lib.ParserTestCase):
    """Tests for the Windows Shortcut (LNK) parser."""

    def testParse(self):
        """Tests the Parse function on an LNK with a link target identifier."""
        parser = winlnk.WinLnkParser()
        storage_writer = self._ParseFile(["NeroInfoTool.lnk"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 7)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test shortcut event data.
        expected_event_values = {
            "creation_time": "2009-06-05T20:13:20.0000000+00:00",
            "data_type": "windows:lnk:link",
            "description": (
                "Nero InfoTool provides you with information about the most "
                "important features of installed drives, inserted discs, installed "
                "software and much more. With Nero InfoTool you can find out all "
                "about your drive and your system configuration."
            ),
            "drive_serial_number": 0x70ECFA33,
            "drive_type": 3,
            "file_attribute_flags": 0x00000020,
            "file_size": 4635160,
            "icon_location": (
                "C:\\\\Program Files (x86)\\\\Nero\\\\Nero 9\\\\Nero InfoTool\\\\"
                "InfoTool.exe"
            ),
            "local_path": (
                "C:\\\\Program Files (x86)\\\\Nero\\\\Nero 9\\\\Nero InfoTool\\\\"
                "InfoTool.exe"
            ),
            "relative_path": (
                "..\\\\..\\\\..\\\\..\\\\..\\\\..\\\\..\\\\..\\\\"
                "Program Files (x86)\\\\Nero\\\\Nero 9\\\\Nero InfoTool\\\\"
                "InfoTool.exe"
            ),
            "volume_label": "OS",
            "working_directory": (
                "C:\\\\Program Files (x86)\\\\Nero\\\\Nero 9\\\\Nero InfoTool"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        # Test shell item event data.
        expected_event_values = {
            "access_time": "2010-01-29T21:30:12+00:00",
            "creation_time": "2009-06-05T20:13:20+00:00",
            "data_type": "windows:shell_item:file_entry",
            "file_reference": "81349-1",
            "long_name": "InfoTool.exe",
            "modification_time": "2009-06-05T20:13:20+00:00",
            "name": "InfoTool.exe",
            "origin": "NeroInfoTool.lnk",
            "shell_item_path": (
                "<My Computer> C:\\\\Program Files (x86)\\\\Nero\\\\Nero 9\\\\"
                "Nero InfoTool\\\\InfoTool.exe"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # Test distributed link tracking event data.
        expected_event_values = {
            "creation_time": "2010-01-29T21:02:17.8401717+00:00",
            "data_type": "windows:distributed_link_tracking:creation",
            "mac_address": "70:5a:b6:16:a5:f3",
            "uuid": "958705b5-0d19-11df-9fe4-705ab616a5f3",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
        self.CheckEventData(event_data, expected_event_values)

    def testParseUnpairedSurrogate(self):
        """Tests the Parse function on an LNK with an unpaired surrogate."""
        parser = winlnk.WinLnkParser()
        storage_writer = self._ParseFile(["unpaired_surrogate.lnk"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test shortcut event data.
        expected_event_values = {
            "creation_time": "2023-07-10T04:01:20.7971076+00:00",
            "data_type": "windows:lnk:link",
            "description": None,
            "drive_serial_number": 0x2CA3D1AE,
            "drive_type": 3,
            "file_attribute_flags": 0x00000020,
            "file_size": 11264,
            "local_path": "C:\\\\test\\\\unicode_U+0000d800_\\U0000d800.exe",
            "relative_path": ".\\\\unicode_U+0000d800_\\U0000d800.exe",
            "working_directory": "C:\\\\test",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # Test shell item event data.
        expected_event_values = {
            "access_time": "2023-07-10T04:01:28+00:00",
            "creation_time": "2023-07-10T04:01:22+00:00",
            "data_type": "windows:shell_item:file_entry",
            "file_reference": "386618-63",
            "long_name": "unicode_U+0000d800_\\U0000d800.exe",
            "modification_time": "2019-12-06T21:29:00+00:00",
            "name": "UNICOD~1.EXE",
            "origin": "unpaired_surrogate.lnk",
            "shell_item_path": (
                "<My Computer> C:\\\\test\\\\unicode_U+0000d800_\\U0000d800.exe"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
