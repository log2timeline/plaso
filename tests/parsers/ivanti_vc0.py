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

    # pylint: disable=protected-access

    def testFileEntryFilter(self):
        """Tests the file entry filter."""
        file_entry_filter = ivanti_vc0.VC0FileEntryFilter()

        for filename in (
            "test.access.vc0",
            "test.admin.vc0",
            "test.diagnosticlog.vc0",
            "test.events.vc0",
            "test.events.vc0.old",
            "test.policytrace.vc0",
            "test.sensorslog.vc0",
            "TEST.EVENTS.VC0",
        ):
            file_entry = _TestFileEntry(filename)
            self.assertTrue(file_entry_filter.Match(file_entry))

        for filename in (
            "events.vc0",
            "log.vc0",
            "log.events.txt",
            "log.events.vc0.tmp",
            "random.bin",
        ):
            file_entry = _TestFileEntry(filename)
            self.assertFalse(file_entry_filter.Match(file_entry))

        self.assertFalse(file_entry_filter.Match(None))

    def testGetLogType(self):
        """Tests the _GetLogType function."""
        parser = ivanti_vc0.IvantiVC0Parser()

        filenames = ["test.access.vc0", "test.access.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "access")

        filenames = ["test.admin.vc0", "test.admin.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "admin")

        filenames = ["test.diagnosticlog.vc0", "test.diagnosticlog.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "diagnosticlog")

        filenames = ["test.events.vc0", "test.events.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "events")

        filenames = ["test.policytrace.vc0", "test.policytrace.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "policytrace")

        filenames = ["test.sensorslog.vc0", "test.sensorslog.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertEqual(log_type, "sensorslog")

        filenames = ["bogus.vc0", "bogus.vc0.old"]
        for filename in filenames:
            log_type = parser._GetLogType(filename)
            self.assertIsNone(log_type)

    def testParseWithLogAccess(self):
        """Tests the Parse function with a log.access.vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.access.vc0"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "authentication_realm": "Root",
            "body": (
                "User login succeeded | web | vpn.example.com | 198.51.100.21 | Pulse "
                "Secure Client | Windows | session-1 | context-users | ... (5 more "
                "fields)"
            ),
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics-access.example.com",
            "line_number": 17,
            "log_type": "access",
            "message_code": "NWC23508",
            "record_identifier": "65c4a660.00000011",
            "recorded_time": "2024-02-08T10:01:04+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithLogAdmin(self):
        """Tests the Parse function with a log.admin.vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.admin.vc0"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "authentication_realm": "Root",
            "body": (
                "Administrator login succeeded | admin-ui | configuration | object-1 | "
                "saved | complete"
            ),
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics-admin.example.com",
            "line_number": 33,
            "log_type": "admin",
            "message_code": "ADM23535",
            "record_identifier": "65c4a670.00000021",
            "recorded_time": "2024-02-08T10:01:20+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithLogEvents(self):
        """Tests the Parse function with a log.events.vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.events.vc0"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

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
            "authentication_realm": "Root",
            "body": "Active Directory configuration server | complete",
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics.example.com",
            "line_number": 1,
            "log_type": "events",
            "message_code": "SYS10306",
            "record_identifier": "65c4a650.00000001",
            "recorded_time": "2024-02-08T10:00:48+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithLogPolicyTrace(self):
        """Tests the Parse function with an empty log.policytrace.vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.policytrace.vc0"], parser)

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

    def testParseWithLogSensorsLog(self):
        """Tests the Parse function with a log.sensorslog.vc0 file."""
        parser = ivanti_vc0.IvantiVC0Parser()
        storage_writer = self._ParseFile(["ivanti_vc0", "log.sensorslog.vc0"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "authentication_realm": "Root",
            "body": "Sensor update completed | integrity | healthy",
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics-sensor.example.com",
            "line_number": 65,
            "log_type": "sensorslog",
            "message_code": "IDP24672",
            "record_identifier": "65c4a690.00000041",
            "recorded_time": "2024-02-08T10:01:52+00:00",
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

    def testParseWithInvalidUtf8(self):
        """Tests the Parse function with invalid UTF-8."""
        parser = ivanti_vc0.IvantiVC0Parser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = b"".join(
            [
                b"\x05\x00\x00\x00\x01\x00\x00\x00",
                b"\x00" * 8184,
                b"65c4a64f.00000001\tics.example.com\tSYS12345\tvc0\t",
                b"Root\t203.0.113.10\tjdoe\tUser login \xff succeeded",
            ]
        )
        file_object = self._CreateFileObject("log.events.vc0", data)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "authentication_realm": "Root",
            "body": "User login \\xff succeeded",
            "data_type": "ivanti:connect_secure:vc0:record",
            "hostname": "ics.example.com",
            "line_number": 1,
            "log_type": None,
            "message_code": "SYS12345",
            "record_identifier": "65c4a64f.00000001",
            "recorded_time": "2024-02-08T10:00:47+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
