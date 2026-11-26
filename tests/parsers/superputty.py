#!/usr/bin/env python3
"""Tests for the SuperPuTTY sessions (Sessions.XML) file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import superputty

from tests.parsers import test_lib


class TestFileEntry:
    """Test file entry."""

    def __init__(self, name):
        """Initializes a test file entry.

        Args:
          name (str): file entry name.
        """
        super().__init__()
        self.name = name


class TestSuperPuTTYSessionsParser(superputty.SuperPuTTYSessionsParser):
    """SuperPuTTY sessions parser with a small maximum file size for testing."""

    _MAXIMUM_FILE_SIZE = 64


class SuperPuTTYSessionsFileEntryFilterTest(test_lib.ParserTestCase):
    """Tests for the SuperPuTTY sessions file entry filter."""

    def testMatch(self):
        """Tests the Match function."""
        file_entry_filter = superputty.SuperPuTTYSessionsFileEntryFilter()

        for filename in (
            "Sessions.XML",
            "sessions.xml",
            "Sessions.20261126_012611.XML",
        ):
            file_entry = TestFileEntry(filename)
            self.assertTrue(file_entry_filter.Match(file_entry))

        for filename in (
            "Sessions.XML.bak",
            "Sessions.backup.XML",
            "SuperPuTTY.settings",
            "typed_history.xml",
        ):
            file_entry = TestFileEntry(filename)
            self.assertFalse(file_entry_filter.Match(file_entry))

        self.assertFalse(file_entry_filter.Match(None))


class SuperPuTTYSessionsParserTest(test_lib.ParserTestCase):
    """Tests for the SuperPuTTY sessions (Sessions.XML) file parser."""

    def testParse(self):
        """Tests the Parse function."""
        parser = superputty.SuperPuTTYSessionsParser()
        storage_writer = self._ParseFile(["superputty", "Sessions.XML"], parser)

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
            "data_type": "superputty:session",
            "extra_arguments": None,
            "hostname": "192.0.2.10",
            "local_path": "C:\\Users\\labadmin\\Documents",
            "port_number": 22,
            "protocol": "SSH",
            "putty_session": "Default Settings",
            "remote_path": "/var/www",
            "session_identifier": "Lab/Servers/web01",
            "session_name": "web01",
            "username": "admin",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "superputty:session",
            "extra_arguments": "-pw NotARealPassword",
            "hostname": "web02.example.com",
            "local_path": None,
            "port_number": 2222,
            "protocol": "SSH",
            "putty_session": "Default Settings",
            "remote_path": None,
            "session_identifier": "Lab/Servers/web02",
            "session_name": "web02",
            "username": "root",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "superputty:session",
            "hostname": "192.0.2.20",
            "port_number": 23,
            "protocol": "Telnet",
            "session_identifier": "Lab/switch01",
            "username": "netops",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "superputty:session",
            "extra_arguments": "-pw NotARealPassword -C",
            "hostname": "198.51.100.1",
            "session_identifier": "router01",
            "username": "operator",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithBackupFile(self):
        """Tests the Parse function with a backup file."""
        parser = superputty.SuperPuTTYSessionsParser()
        storage_writer = self._ParseFile(
            ["superputty", "Sessions.20261126_012611.XML"], parser
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # In this backup the switch01 session still uses SSH and has no username.
        expected_event_values = {
            "data_type": "superputty:session",
            "hostname": "192.0.2.20",
            "port_number": 23,
            "protocol": "SSH",
            "session_identifier": "Lab/switch01",
            "username": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseFileObjectWithUnsupportedData(self):
        """Tests the ParseFileObject function with unsupported data."""
        parser = superputty.SuperPuTTYSessionsParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject(
            "Sessions.XML", b"This is not a SuperPuTTY sessions file.\r\n"
        )
        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)

        # Test with XML data with another root element.
        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'<?xml version="1.0" encoding="utf-8"?>\r\n'
                b"<ArrayOfLayoutData>\r\n"
                b"</ArrayOfLayoutData>"
            ),
        )
        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)

        # Test with XML data with a document type declaration.
        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'<?xml version="1.0" encoding="utf-8"?>\r\n'
                b'<!DOCTYPE ArrayOfSessionData [<!ENTITY host "192.0.2.1">]>\r\n'
                b'<ArrayOfSessionData><SessionData Host="&host;" />'
                b"</ArrayOfSessionData>"
            ),
        )
        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)

    def testParseFileObjectWithByteOrderMark(self):
        """Tests the ParseFileObject function with an UTF-8 byte-order mark."""
        parser = superputty.SuperPuTTYSessionsParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'\xef\xbb\xbf<?xml version="1.0" encoding="utf-8"?>\r\n'
                b"<ArrayOfSessionData>\r\n"
                b'  <SessionData SessionId="router01" Host="198.51.100.1" '
                b'Port="22" Proto="SSH" />\r\n'
                b"</ArrayOfSessionData>"
            ),
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseFileObjectWithUnsupportedEncoding(self):
        """Tests the ParseFileObject function with an unsupported encoding."""
        parser = superputty.SuperPuTTYSessionsParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'<?xml version="1.0" encoding="bogus"?>\r\n'
                b"<ArrayOfSessionData>\r\n"
                b"</ArrayOfSessionData>"
            ),
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testParseFileObjectWithUnsupportedFileSize(self):
        """Tests the ParseFileObject function with an unsupported file size."""
        parser = TestSuperPuTTYSessionsParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'<?xml version="1.0" encoding="utf-8"?>\r\n'
                b"<ArrayOfSessionData>\r\n"
                b'  <SessionData SessionId="router01" Host="198.51.100.1" '
                b'Port="22" Proto="SSH" />\r\n'
                b"</ArrayOfSessionData>"
            ),
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testParseFileObjectWithMalformedData(self):
        """Tests the ParseFileObject function with malformed data."""
        parser = superputty.SuperPuTTYSessionsParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        # Test with truncated XML data.
        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'\xef\xbb\xbf<?xml version="1.0" encoding="utf-8"?>\r\n'
                b"<ArrayOfSessionData>\r\n"
                b'  <SessionData SessionId="router01" Host="198.51.100.1"'
            ),
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        # Test with an unsupported port number.
        file_object = self._CreateFileObject(
            "Sessions.XML",
            (
                b'<?xml version="1.0" encoding="utf-8"?>\r\n'
                b"<ArrayOfSessionData>\r\n"
                b'  <SessionData SessionId="router01" Host="198.51.100.1" '
                b'Port="bogus" Proto="SSH" />\r\n'
                b"</ArrayOfSessionData>"
            ),
        )
        parser.ParseFileObject(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        expected_event_values = {
            "data_type": "superputty:session",
            "hostname": "198.51.100.1",
            "port_number": None,
            "session_identifier": "router01",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
