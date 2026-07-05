#!/usr/bin/env python3
"""Tests for the Systemd Journal parser."""

import io
import unittest

from plaso.containers import warnings
from plaso.lib import errors
from plaso.parsers import systemd_journal

from tests.parsers import test_lib


class SystemdJournalParserTest(test_lib.ParserTestCase):
    """Tests for the Systemd Journal parser."""

    # pylint: disable=protected-access

    def testParseDataObjectWithCorruptCompressedData(self):
        """Tests _ParseDataObject raises ParseError on corrupt compressed data."""
        parser = systemd_journal.SystemdJournalParser()

        def _data_object(flags, payload):
            # A 64-byte DATA object header (object_type=1, object_flags=flags,
            # 6 reserved bytes, data_size, then 6 unused uint64 fields) followed
            # by a corrupt compressed payload.
            header = (
                bytes([1, flags])
                + b"\x00" * 6
                + (64 + len(payload)).to_bytes(8, "little")
                + b"\x00" * 48
            )
            return io.BytesIO(header + payload)

        file_object = _data_object(parser._OBJECT_COMPRESSED_FLAG_XZ, b"corrupt-xz")
        with self.assertRaises(errors.ParseError):
            parser._ParseDataObject(file_object, 0)

        file_object = _data_object(
            parser._OBJECT_COMPRESSED_FLAG_LZ4,
            b"\x10\x00\x00\x00\x00\x00\x00\x00corrupt-lz4",
        )
        with self.assertRaises(errors.ParseError):
            parser._ParseDataObject(file_object, 0)

    def testParseKeyValuePair(self):
        """Tests the _ParseKeyValuePair function with text and binary values."""
        parser = systemd_journal.SystemdJournalParser()
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        key, value = parser._ParseKeyValuePair(parser_mediator, b"MESSAGE=hello world")
        self.assertEqual(key, "MESSAGE")
        self.assertEqual(value, "hello world")

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A key value pair containing invalid UTF-8 code points must decode with them
        # escaped and produce an extraction warning.
        key, value = parser._ParseKeyValuePair(
            parser_mediator, b"MESSAGE=abc\xff\xfexyz"
        )
        self.assertEqual(key, "MESSAGE")
        self.assertEqual(value, "abc\\xff\\xfexyz")

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testParse(self):
        """Tests the Parse function."""
        parser = systemd_journal.SystemdJournalParser()
        storage_writer = self._ParseFile(
            ["systemd", "journal", "system.journal"], parser
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2101)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "systemd:journal",
            "boot_identifier": "493676ee7ee04cff9afb308244ef893c",
            "command_line": "/sbin/init splash",
            "executable": "/lib/systemd/systemd",
            "facility": "system daemons",
            "group_identifier": "0",
            "hostname": "test-VirtualBox",
            "machine_identifier": "a447b9eff9fe40a890e8e376e92a4ede",
            "message_body": "Started User Manager for UID 1000.",
            "pid": "1",
            "process_name": "systemd",
            "recorded_time": "2017-01-27T09:40:55.855726+00:00",
            "reporter": "systemd",
            "severity": "INFO",
            "systemd_unit": "init.scope",
            "transport": "journal",
            "user_identifier": "0",
            "written_time": "2017-01-27T09:40:55.913258+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test a XZ compressed data log entry.
        expected_event_values = {
            "data_type": "systemd:journal",
            "boot_identifier": "493676ee7ee04cff9afb308244ef893c",
            "facility": "user-level message",
            "group_identifier": "0",
            "hostname": "test-VirtualBox",
            "machine_identifier": "a447b9eff9fe40a890e8e376e92a4ede",
            "message_body": "a" * 692,
            "pid": "22921",
            "process_name": "logger",
            "recorded_time": "2017-02-06T16:24:32.562231+00:00",
            "reporter": "root",
            "severity": "NOTICE",
            "transport": "syslog",
            "user_identifier": "0",
            "written_time": "2017-02-06T16:24:32.564585+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2098)
        self.CheckEventData(event_data, expected_event_values)

    def testParseLZ4(self):
        """Tests the Parse function on a journal with LZ4 compressed events."""
        parser = systemd_journal.SystemdJournalParser()
        storage_writer = self._ParseFile(
            ["systemd", "journal", "system.journal.lz4"], parser
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 85)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "systemd:journal",
            "audit_login_identifier": "1000",
            "boot_identifier": "02e8c96371d240b7b3934b11b08a120e",
            "command_line": "/lib/systemd/systemd --user",
            "executable": "/lib/systemd/systemd",
            "facility": "system daemons",
            "group_identifier": "1000",
            "hostname": "testlol",
            "machine_identifier": "cf624987d3b145a79c35ae3874368fc7",
            "message_body": "Reached target Paths.",
            "pid": "822",
            "process_name": "systemd",
            "recorded_time": "2018-07-03T15:00:16.679635+00:00",
            "reporter": "systemd",
            "severity": "INFO",
            "systemd_unit": "user@1000.service",
            "transport": "journal",
            "user_identifier": "1000",
            "written_time": "2018-07-03T15:00:16.682340+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test the reporter fallback to _COMM when SYSLOG_IDENTIFIER is absent.
        # This entry has no SYSLOG_IDENTIFIER, so reporter (and the pid, which is
        # only set for non-kernel reporters) are derived from the trusted _COMM.
        expected_event_values = {
            "data_type": "systemd:journal",
            "audit_login_identifier": "1000",
            "facility": None,
            "hostname": "testlol",
            "pid": "1485",
            "process_name": "indicator-sound",
            "recorded_time": "2018-07-03T15:00:21.873337+00:00",
            "reporter": "indicator-sound",
            "severity": "WARNING",
            "systemd_unit": "user@1000.service",
            "transport": "journal",
            "user_identifier": "1000",
            "written_time": "2018-07-03T15:00:21.875704+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 39)
        self.CheckEventData(event_data, expected_event_values)

        # Test a LZ4 compressed data log entry.
        # The text used in the test message was trippled to make it long enough to
        # trigger the LZ4 compression. Also see:
        # https://github.com/systemd/systemd/issues/6237
        expected_message_body_parts = [" textual user names."]
        expected_message_body_parts.extend(
            (
                "  Yes, as you found out 0day is not a valid username. I wonder which "
                "tool permitted you to create it in the first place. Note that not "
                "permitting numeric first characters is done on purpose: to avoid "
                "ambiguities between numeric UID and textual user names."
            )
            * 3
        )
        expected_message_body = "".join(expected_message_body_parts)

        expected_event_values = {
            "data_type": "systemd:journal",
            "boot_identifier": "02e8c96371d240b7b3934b11b08a120e",
            "facility": "user-level message",
            "group_identifier": "1000",
            "hostname": "testlol",
            "machine_identifier": "cf624987d3b145a79c35ae3874368fc7",
            "message_body": expected_message_body,
            "pid": "34757",
            "recorded_time": "2018-07-03T15:19:04.664754+00:00",
            "reporter": "test",
            "severity": "NOTICE",
            "transport": "syslog",
            "user_identifier": "1000",
            "written_time": "2018-07-03T15:19:04.667807+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 84)
        self.CheckEventData(event_data, expected_event_values)

    def testParseCompactZSTD(self):
        """Tests the Parse function on a journal with compact mode and ZSTD."""
        parser = systemd_journal.SystemdJournalParser()
        storage_writer = self._ParseFile(
            ["systemd", "journal", "user-1000.journal"], parser
        )
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

        large_string = "A" * 512

        # This journal was generated on stdout transport: it has no
        # SYSLOG_FACILITY (facility stays None) and no _SOURCE_REALTIME_TIMESTAMP
        # (recorded_time stays None).
        expected_event_values = {
            "data_type": "systemd:journal",
            "boot_identifier": "7dd8f8967ea94fec9efa46beed3d2a71",
            "facility": None,
            "group_identifier": "1000",
            "hostname": "DESKTOP-QCDE2BT",
            "machine_identifier": "9e4a892d275848e797b10057152ae1bf",
            "message_body": f"Some large string: {large_string:s}",
            "pid": "197",
            "process_name": "cat",
            "recorded_time": None,
            "reporter": "testapp",
            "severity": "INFO",
            "transport": "stdout",
            "user_identifier": "1000",
            "written_time": "2023-09-26T07:42:46.445209+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseDirty(self):
        """Tests the Parse function on a 'dirty' journal file."""
        parser = systemd_journal.SystemdJournalParser()

        storage_writer = self._ParseFile(
            [
                "systemd",
                "journal",
                "system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE",
            ],
            parser,
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2211)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 46)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "systemd:journal",
            "boot_identifier": "978fdbbbe8ab4f1d834efb2899083415",
            "command_line": "/lib/systemd/systemd-journald",
            "executable": "/lib/systemd/systemd-journald",
            "facility": "system daemons",
            "group_identifier": "0",
            "hostname": "test-VirtualBox",
            "machine_identifier": "49cd46492584496585e147de34ed5816",
            "message_body": (
                "Runtime journal (/run/log/journal/) is 1.2M, max 9.9M, 8.6M " "free."
            ),
            "pid": "569",
            "process_name": "systemd-journal",
            "reporter": "systemd-journald",
            "severity": "INFO",
            "systemd_unit": "systemd-journald.service",
            "transport": "driver",
            "user_identifier": "0",
            "written_time": "2016-10-24T13:20:01.063423+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        generator = storage_writer.GetAttributeContainers(
            warnings.ExtractionWarning.CONTAINER_TYPE
        )
        test_warnings = list(generator)
        test_warning = test_warnings[0]
        self.assertIsNotNone(test_warning)

        expected_message = (
            "Unable to parse journal entry at offset: 0x0041bfb0 with error: "
            "object offset should be after hash tables (0 < 2527472)"
        )
        self.assertEqual(test_warning.message, expected_message)

        # The 46 warnings are 1 corrupt entry pointer plus 45 unused/zeroed objects in
        # the unclean tail.
        unsupported_warnings = [
            warning
            for warning in test_warnings
            if "Unsupported object type: 0" in warning.message
        ]
        self.assertEqual(len(unsupported_warnings), 45)

        expected_message = (
            "Unable to parse journal entry at offset: 0x004287a0 with error: "
            "Unsupported object type: 0"
        )
        self.assertEqual(test_warnings[-1].message, expected_message)


if __name__ == "__main__":
    unittest.main()
