#!/usr/bin/env python3
"""Parser test for utmp files."""

import unittest

from plaso.containers import warnings
from plaso.parsers import utmp

from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
    """The unit test for utmp parser."""

    def testParseUtmpFile(self):
        """Tests the Parse function on a utmp file."""
        parser = utmp.UtmpParser()
        storage_writer = self._ParseFile(["utmp"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 14)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "linux:utmp:event",
            "exit_status": 0,
            "hostname": "localhost",
            "ip_address": "0.0.0.0",
            "pid": 1115,
            "terminal_identifier": 52,
            "terminal": "tty4",
            "type": 6,
            "username": "LOGIN",
            "written_time": "2013-12-13T14:45:09.000000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWtmpFile(self):
        """Tests the Parse function on a wtmp file."""
        parser = utmp.UtmpParser()
        storage_writer = self._ParseFile(["wtmp.1"], parser)

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

        expected_event_values = {
            "data_type": "linux:utmp:event",
            "exit_status": 0,
            "hostname": "10.10.122.1",
            "ip_address": "10.10.122.1",
            "pid": 20060,
            "terminal": "pts/32",
            "terminal_identifier": 842084211,
            "type": 7,
            "username": "userA",
            "written_time": "2011-12-01T17:36:38.432935+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseCorruptUtmpFile(self):
        """Tests that corrupt records do not abort parsing of the rest.

        The file is: valid (alice), two consecutive unsupported-type records,
        valid (bob), then a truncated trailing record.
        """
        parser = utmp.UtmpParser()
        storage_writer = self._ParseFile(["utmp_corrupted"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        # The valid record after the two skipped corrupt records is recovered;
        # its offset (1152) proves it was read past them. The truncated trailing
        # record is treated as the end of the file (no extra warning).
        expected_event_values = {
            "data_type": "linux:utmp:event",
            "hostname": "10.0.0.5",
            "ip_address": "10.0.0.5",
            "offset": 1152,
            "pid": 3003,
            "terminal": "pts/0",
            "type": 7,
            "username": "bob",
            "written_time": "2023-11-14T22:46:40.000000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        generator = storage_writer.GetAttributeContainers(
            warnings.ExtractionWarning.CONTAINER_TYPE
        )
        test_warnings = list(generator)
        self.assertEqual(
            test_warnings[0].message,
            "Unable to parse utmp entry at offset: 0x00000180, skipping record",
        )
        self.assertEqual(
            test_warnings[1].message,
            "Unable to parse utmp entry at offset: 0x00000300, skipping record",
        )

    def testParse64bitUtmpFile(self):
        """Tests the Parse function on a 64-bit (aarch64) utmp file.

        The libc6 utmp record is 400 bytes on 64-bit builds without 32-bit time
        compatibility (e.g. aarch64), versus 384 bytes on x86-64. This sample was
        generated on aarch64: a boot record, a user login, and a logout.
        """
        parser = utmp.UtmpParser()
        storage_writer = self._ParseFile(["utmp_64bit"], parser)

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

        # Record 0: boot.
        expected_event_values = {
            "data_type": "linux:utmp:event",
            "hostname": "localhost",
            "ip_address": "0.0.0.0",
            "offset": 0,
            "terminal": "system boot",
            "type": 2,
            "username": "reboot",
            "written_time": "2020-01-01T00:00:00.000000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Record 1: user login. offset 400 proves the parser advanced by the
        # 64-bit record size (400 bytes) rather than 384.
        expected_event_values = {
            "data_type": "linux:utmp:event",
            "hostname": "example.com",
            "ip_address": "127.0.0.1",
            "offset": 400,
            "pid": 1234,
            "terminal": "pts/0",
            "type": 7,
            "username": "testuser",
            "written_time": "2020-01-01T00:01:00.500000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
