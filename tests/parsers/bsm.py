#!/usr/bin/env python3
"""Tests for Basic Security Module (BSM) file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import bsm

from tests.parsers import test_lib


class MacOSBSMParserTest(test_lib.ParserTestCase):
    """Tests for Basic Security Module (BSM) file parser."""

    def testParse(self):
        """Tests the Parse function on a MacOS BSM file."""
        parser = bsm.BSMParser()
        storage_writer = self._ParseFile(["apple.bsm"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 54)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "bsm:entry",
            "event_type": 45029,
            "extra_tokens": [
                {"AUT_TEXT": {"text": "launchctl::Audit recovery"}},
                {"AUT_PATH": {"path": "/var/audit/20131104171720.crash_recovery"}},
                {
                    "AUT_RETURN32": {
                        "call_status": 0,
                        "error": "Success",
                        "token_status": 0,
                    }
                },
            ],
            "return_value": (
                "{'error': 'Success', 'token_status': 0, 'call_status': 0}"
            ),
            "written_time": "2013-11-04T18:36:20.000381+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


class OpenBSMParserTest(test_lib.ParserTestCase):
    """Tests for Basic Security Module (BSM) file parser."""

    def testParse(self):
        """Tests the Parse function on a "generic" BSM file."""
        parser = bsm.BSMParser()
        storage_writer = self._ParseFile(["openbsm.bsm"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 50)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "bsm:entry",
            "event_type": 0,
            "extra_tokens": [
                {
                    "AUT_ARG32": {
                        "is": 2882400000,
                        "num_arg": 3,
                        "string": "test_arg32_token",
                    }
                }
            ],
            "return_value": None,
            "written_time": "2008-12-28T15:12:18.000131+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def _ParseData(self, data):
        """Parses BSM data.

        Args:
          data (bytes): BSM data.

        Returns:
          FakeStorageWriter: storage writer.
        """
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)
        file_object = self._CreateFileObject("openbsm.bsm", data)

        parser = bsm.BSMParser()
        parser.ParseFileObject(parser_mediator, file_object)

        return storage_writer

    def testParseFileObjectWithCorruptedRecord(self):
        """Tests the ParseFileObject function with a corrupted event record."""
        test_file_path = self._GetTestFilePath(["openbsm.bsm"])
        self._SkipIfPathNotExists(test_file_path)

        with open(test_file_path, "rb") as file_object:
            test_data = bytearray(file_object.read())

        # The second event record starts at offset 0x32 with a 18 byte header
        # token and its first token after the header token is at offset 0x44.
        self.assertEqual(test_data[0x32], 0x14)
        self.assertEqual(test_data[0x44], 0x21)

        expected_event_values = {
            "data_type": "bsm:entry",
            "event_type": 0,
            "offset": 0x59,
            "record_length": 41,
        }

        # Test with an unsupported token type in the second event record.
        corrupted_data = bytearray(test_data)
        corrupted_data[0x44] = 0xFF

        storage_writer = self._ParseData(bytes(corrupted_data))

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 49)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        warning = storage_writer.GetAttributeContainerByIndex("extraction_warning", 0)
        self.assertEqual(
            warning.message,
            "unable to parse event record at offset: 0x00000032 with error: "
            "Unsupported token type: 0xff",
        )

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Test with an unsupported header token type in the second event record.
        corrupted_data = bytearray(test_data)
        corrupted_data[0x32] = 0x00

        storage_writer = self._ParseData(bytes(corrupted_data))

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 49)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Test with an unsupported header token type in the first event record.
        corrupted_data = bytearray(test_data)
        corrupted_data[0] = 0x00

        with self.assertRaises(errors.WrongParser):
            self._ParseData(bytes(corrupted_data))


if __name__ == "__main__":
    unittest.main()
