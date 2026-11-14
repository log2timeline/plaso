#!/usr/bin/env python3
"""Tests for the Microsoft Defender MpEngineDb (mpenginedb.db) parser."""

import os
import unittest

from plaso.lib import errors
from plaso.parsers import mpenginedb

from tests.parsers import test_lib


class _TestFileEntry:
    """Test file entry."""

    def __init__(self, name):
        """Initializes a test file entry.

        Args:
          name (str): name of the file entry.
        """
        super().__init__()
        self.name = name


class MpEngineDbParserTest(test_lib.ParserTestCase):
    """Tests for the Microsoft Defender MpEngineDb parser."""

    # pylint: disable=protected-access

    def _ReadTestFile(self, filename):
        """Reads a test file.

        Args:
          filename (str): name of the file in the test data directory.

        Returns:
          bytes: content of the test file.
        """
        test_file_path = self._GetTestFilePath([filename])
        self._SkipIfPathNotExists(test_file_path)

        with open(test_file_path, "rb") as file_object:
            return file_object.read()

    def testFileEntryFilter(self):
        """Tests the file entry filter."""
        parser = mpenginedb.MpEngineDbParser()
        file_entry_filter = list(parser.FILTERS)[0]

        self.assertTrue(file_entry_filter.Match(_TestFileEntry("mpenginedb.db")))
        self.assertTrue(file_entry_filter.Match(_TestFileEntry("MpEngineDb.db")))

        self.assertFalse(file_entry_filter.Match(_TestFileEntry("mpenginedb.db-wal")))
        self.assertFalse(file_entry_filter.Match(_TestFileEntry("History")))
        self.assertFalse(file_entry_filter.Match(None))

    def testDecryptDatabase(self):
        """Tests the _DecryptDatabase function."""
        parser = mpenginedb.MpEngineDbParser()

        database_data = self._ReadTestFile("mpenginedb.db")
        wal_data = self._ReadTestFile("mpenginedb.db-wal")

        decrypted_data = parser._DecryptDatabase(database_data, None)
        self.assertEqual(decrypted_data[:15], b"SQLite format 3")
        self.assertEqual(len(decrypted_data), len(database_data))

        decrypted_wal_data = parser._DecryptDatabase(database_data, wal_data)
        self.assertEqual(decrypted_wal_data[:15], b"SQLite format 3")
        # The WAL of the test file shrinks the database from 184 to 171 pages.
        self.assertNotEqual(len(decrypted_wal_data), len(decrypted_data))
        self.assertNotEqual(decrypted_wal_data, decrypted_data)

        # A WAL with a corrupt header is ignored.
        corrupt_wal_data = bytearray(wal_data)
        corrupt_wal_data[8] ^= 0xFF
        decrypted_corrupt_data = parser._DecryptDatabase(
            database_data, bytes(corrupt_wal_data)
        )
        self.assertEqual(decrypted_corrupt_data, decrypted_data)

        # A WAL that is truncated inside a frame only applies the preceding frames.
        truncated_wal_data = wal_data[: 32 + (24 + 4096) * 10 + 100]
        decrypted_truncated_data = parser._DecryptDatabase(
            database_data, truncated_wal_data
        )
        self.assertEqual(decrypted_truncated_data[:15], b"SQLite format 3")

    def testDecryptDatabaseWithUnknownKey(self):
        """Tests the _DecryptDatabase function with unsupported data."""
        parser = mpenginedb.MpEngineDbParser()

        with self.assertRaises(errors.WrongParser):
            parser._DecryptDatabase(b"SQLite format 3\x00" + bytes(4096), None)

        with self.assertRaises(errors.WrongParser):
            parser._DecryptDatabase(os.urandom(8192), None)

        with self.assertRaises(errors.WrongParser):
            parser._DecryptDatabase(b"too small", None)

    def testParse(self):
        """Tests the Parse function."""
        parser = mpenginedb.MpEngineDbParser()
        storage_writer = self._ParseFile(["mpenginedb.db"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        # AttributePersistContext: 999, BackupProcessInfo: 1837, FileHashes: 3,
        # FileLowFiAsync: 12 and RollingQueuesValues: 65.
        self.assertEqual(number_of_event_data, 2916)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "context": "processed",
            "data_type": "windows:defender:mpenginedb:attribute_persist_context",
            "expiration_time": "2027-01-11T07:16:59.9078663+00:00",
            "insertion_time": "2026-11-12T07:16:59.9078790+00:00",
            "path": (
                "ENG:OFNPROCESSED:c:\\program files\\windowsapps\\"
                "microsoft.windowsfeedbackhub_1.2401.20253.0_x64__8wekyb3d8bbwe\\"
                "assets\\feedbackhubsplashscreen.scale-200_altform-colorful.png"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:defender:mpenginedb:backup_process_info",
            "impacted_namespaces": None,
            "instance_time": "2026-11-06T05:41:48.0594788+00:00",
            "next_usn": 46677456,
            "path": "C:\\Windows\\System32\\svchost.exe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 999)
        self.CheckEventData(event_data, expected_event_values)

        # Note that the MD5 hash is stored in the column named SHA1 and the SHA-1
        # hash in the column named MD5.
        expected_event_values = {
            "data_type": "windows:defender:mpenginedb:file_hash",
            "instance_time": "2026-11-06T21:48:08.8014236+00:00",
            "md5_hash": "2ffd9717cf6df99d2402cd62662d6541",
            "mft_entry": 35754,
            "mft_sequence_number": 5,
            "sha1_hash": "c34da1b677a4924a3c780b6f3cb47fef0e80b667",
            "sha256_hash": (
                "d5e2f177b61d8757e5f8ec29538d6b344f394dc5eda4e30675f22c352929c4a1"
            ),
            "ssdeep_hash": (
                "3072:ExELHU4wV49XZiR5CC+fXcRKt1bHQ5iDZApilLCAreXLUsXYgcu3/oMfI:"
                "9TtwV4FCz+kILHQKAIAugcuPbf"
            ),
            "usn": 56214888,
            "volume_serial_number": 539055321,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2836)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:defender:mpenginedb:low_fidelity",
            "instance_time": "2026-11-09T05:44:25.3727834+00:00",
            "is_synchronous": True,
            "path": "C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\PCWC576.xml",
            "signature_sequence": 141730041757388,
            "signature_sha1": "be1de0776b0d5028a57e0ebda0fbb8dc49d8d2dd",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2839)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:defender:mpenginedb:rolling_queue",
            "entry_key": "c:\\windows\\sysmondrv.sys",
            "expiration_time": "2027-11-01T06:46:59.9386278+00:00",
            "insertion_time": "2026-11-06T06:46:59.9386278+00:00",
            "process_identifier": 5704,
            "process_image": "\\Device\\HarddiskVolume3\\lab\\Sysmon64.exe",
            "process_start_time": "2026-11-06T06:46:55.6769521+00:00",
            "queue_name": "RQ_RecentExecDropped",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2851)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
