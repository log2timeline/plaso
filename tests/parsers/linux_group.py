#!/usr/bin/env python3
"""Tests for the group database (/etc/group) file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import linux_group

from tests.parsers import test_lib


class LinuxGroupParserTest(test_lib.ParserTestCase):
    """Tests for the group database (/etc/group) file parser."""

    def _ParseData(self, data):
        """Parses data with the parser.

        Args:
          data (bytes): data.

        Returns:
          FakeStorageWriter: storage writer.

        Raises:
          WrongParser: when the data cannot be parsed.
        """
        parser = linux_group.LinuxGroupParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("group", data)
        parser.ParseFileObject(parser_mediator, file_object)

        return storage_writer

    def testParse(self):
        """Tests the Parse function."""
        parser = linux_group.LinuxGroupParser()
        storage_writer = self._ParseFile(["group"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "linux:group:entry",
            "group_identifier": 0,
            "group_name": "root",
            "members": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "linux:group:entry",
            "group_identifier": 998,
            "group_name": "docker",
            "members": ["alice", "bob"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithCommentsAndInvalidEntry(self):
        """Tests the Parse function with comments and an invalid entry."""
        storage_writer = self._ParseData(
            b"##\n"
            b"# Group Database\n"
            b"##\n"
            b"nobody:*:-2:\n"
            b"wheel:*:0:root\n"
            b"staff:*:20\n"
            b"\n"
            b"admin:*:80:root,carol\n"
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "data_type": "linux:group:entry",
            "group_identifier": -2,
            "group_name": "nobody",
            "members": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "linux:group:entry",
            "group_identifier": 80,
            "group_name": "admin",
            "members": ["root", "carol"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithNonMatchingFormats(self):
        """Tests the Parse function with formats that should not match."""
        # Check a password database (/etc/passwd) file.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"root:x:0:0:root:/root:/bin/bash\n")

        # Check a file with a non-numeric group identifier.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"key:value:other:value\n")

        # Check a file with a group identifier that is not a number.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"root:x:-:\n")

        # Check a file with a line with white space and 3 colons.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"Start-Date: 2019-07-10  16:38:08\n")

        # Check a file with an empty group name.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b":x:0:\n")

        # Check a file with only comment lines.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"# root:x:0:\n")

        # Check a file with more leading comment lines than supported.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"#\n" * 21 + b"root:x:0:\n")


if __name__ == "__main__":
    unittest.main()
