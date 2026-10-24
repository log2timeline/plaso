#!/usr/bin/env python3
"""Tests the for bodyfile parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import bodyfile

from tests.parsers import test_lib


class BodyfileTest(test_lib.ParserTestCase):
    """Tests the for bodyfile parser."""

    def testParse(self):
        """Tests the Parse function."""
        parser = bodyfile.BodyfileParser()
        storage_writer = self._ParseFile(["bodyfile", "bodyfile"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 24)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test this entry:
        # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
        # 1337961584|1337961585|0

        expected_event_values = {
            "access_time": "2012-05-25T15:59:43",
            "change_time": "2012-05-25T15:59:45",
            "creation_time": None,
            "data_type": "fs:bodyfile:entry",
            "filename": "/a_directory/another_file",
            "group_identifier": 5000,
            "inode": 16,
            "modification_time": "2012-05-25T15:59:44",
            "owner_identifier": "151107",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseOnCorruptFile(self):
        """Tests the Parse function on a corrupt bodyfile."""
        parser = bodyfile.BodyfileParser()
        storage_writer = self._ParseFile(["bodyfile", "bodyfile.corrupt"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Event data extracted from line with unescaped \r character.
        expected_event_values = {
            "access_time": "2012-05-25T16:00:53",
            "change_time": "2012-05-25T16:01:03",
            "creation_time": None,
            "data_type": "fs:bodyfile:entry",
            "filename": "/passwords\r.txt",
            "inode": 15,
            "modification_time": "2012-05-25T16:00:53",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Event data extracted from line with unescaped \\ character.
        expected_event_values = {
            "access_time": "2021-01-12T12:26:01",
            "change_time": "2019-03-19T04:37:22",
            "creation_time": "2019-03-19T04:37:22",
            "data_type": "fs:bodyfile:entry",
            "filename": "/Windows\\System32",
            "inode": 75520,
            "modification_time": "2021-01-12T12:26:01",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithUnpairedSurrogatesOnFirstLine(self):
        """Tests the Parse function with an unpaired surrogate on line 0."""
        parser = bodyfile.BodyfileParser()

        # UTF-8 encoded line with 3-byte CESU-8 sequence (\xed\xa0\x80) for U+D800.
        bodyfile_data = (
            b"0|/test/unicode_U+0000d800_\xed\xa0\x80.txt|15|r/rr--------|"
            b"151107|5000|116|1337961653|1337961653|1337961663|0\n"
        )
        file_object = self._CreateFileObject("bodyfile.surrogate", bodyfile_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "access_time": "2012-05-25T16:00:53",
            "change_time": "2012-05-25T16:01:03",
            "creation_time": None,
            "data_type": "fs:bodyfile:entry",
            "filename": "/test/unicode_U+0000d800_\\U0000d800.txt",
            "inode": 15,
            "modification_time": "2012-05-25T16:00:53",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        self.assertTrue(getattr(event_data, "_corrupted"))

    def testParseWithUnpairedSurrogatesOnSubsequentLines(self):
        """Tests the Parse function with an unpaired surrogate on line 1."""
        parser = bodyfile.BodyfileParser()

        bodyfile_data = (
            b"0|/normal_file1.txt|12|d/drwxr-xr-x|151107|5000|1024|1337961564|"
            b"1337961563|1337961563|0\n"
            b"0|/test/file_\xed\xa0\x80.txt|15|r/rr--------|151107|5000|116|"
            b"1337961653|1337961653|1337961663|0\n"
            b"0|/normal_file2.txt|16|r/rr--------|151107|5000|116|1337961653|"
            b"1337961653|1337961663|0\n"
        )
        file_object = self._CreateFileObject("bodyfile.surrogate", bodyfile_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        # Confirm that parsing continues through the end of the file.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertFalse(getattr(event_data, "_corrupted"))

        expected_event_values = {
            "data_type": "fs:bodyfile:entry",
            "filename": "/test/file_\\U0000d800.txt",
            "inode": 15,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        self.assertTrue(getattr(event_data, "_corrupted"))

        expected_event_values = {
            "data_type": "fs:bodyfile:entry",
            "filename": "/normal_file2.txt",
            "inode": 16,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        self.assertFalse(getattr(event_data, "_corrupted"))

    def testParseWithPreEscapedSurrogates(self):
        """Tests the Parse function on a bodyfile with pre-escaped surrogate strings."""
        parser = bodyfile.BodyfileParser()

        bodyfile_data = (
            b"0|/test/file_\\U0000d800.txt|15|r/rr--------|151107|5000|116|"
            b"1337961653|1337961653|1337961663|0\n"
            b"0|/test/file_\\ud800.txt|16|r/rr--------|151107|5000|116|"
            b"1337961653|1337961653|1337961663|0\n"
        )
        file_object = self._CreateFileObject("bodyfile.pre_escaped", bodyfile_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        for event_data in storage_writer.GetAttributeContainers("event_data"):
            self.assertFalse(getattr(event_data, "_corrupted"))

        # Confirm literal text escapes are not double-escaped.
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.filename, "/test/file_\\U0000d800.txt")

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.assertEqual(event_data.filename, "/test/file_\\ud800.txt")

    def testParseWithMalformedUTF8(self):
        """Tests the Parse function on a bodyfile with invalid UTF-8 bytes."""
        parser = bodyfile.BodyfileParser()

        bodyfile_data = (
            b"0|/test/file_\xff.txt|15|r/rr--------|151107|5000|116|"
            b"1337961653|1337961653|1337961663|0\n"
        )
        file_object = self._CreateFileObject("bodyfile.malformed", bodyfile_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

    def testParseWithSymbolicLinkTargetUnpairedSurrogates(self):
        """Tests the Parse function with a symlink containing a surrogate."""
        parser = bodyfile.BodyfileParser()

        bodyfile_data = (
            b"0|/link_\xed\xa0\x80 -> /target_\xed\xa0\x80.txt|16|l/lrwxrwxrwx|"
            b"151107|5000|27|1337961653|1337961653|1337961663|0\n"
        )
        file_object = self._CreateFileObject("bodyfile.symlink", bodyfile_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "access_time": "2012-05-25T16:00:53",
            "change_time": "2012-05-25T16:01:03",
            "creation_time": None,
            "data_type": "fs:bodyfile:entry",
            "filename": "/link_\\U0000d800",
            "group_identifier": 5000,
            "inode": 16,
            "modification_time": "2012-05-25T16:00:53",
            "owner_identifier": "151107",
            "symbolic_link_target": "/target_\\U0000d800.txt",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        self.assertTrue(getattr(event_data, "_corrupted"))


if __name__ == "__main__":
    unittest.main()
