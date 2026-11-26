#!/usr/bin/env python3
"""Tests for the FileZilla site manager (sitemanager.xml) file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import filezilla

from tests.parsers import test_lib


class FileZillaSiteManagerParserTest(test_lib.ParserTestCase):
    """Tests for the FileZilla site manager (sitemanager.xml) file parser."""

    def _ParseData(self, data):
        """Parses data with the FileZilla site manager parser.

        Args:
          data (bytes): data to parse.

        Returns:
          FakeStorageWriter: storage writer.
        """
        parser = filezilla.FileZillaSiteManagerParser()
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)
        file_object = self._CreateFileObject("sitemanager.xml", data)

        parser.ParseFileObject(parser_mediator, file_object)

        return storage_writer

    def testParse(self):
        """Tests the Parse function."""
        parser = filezilla.FileZillaSiteManagerParser()
        storage_writer = self._ParseFile(["filezilla_sitemanager.xml"], parser)

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
            "comments": "Staging server of the customer",
            "data_type": "filezilla:site_manager:site",
            "folder_path": "Customers",
            "hostname": "sftp.example.org",
            "key_file": None,
            "local_directory": None,
            "logon_type": 1,
            "name": "Customer staging",
            "port_number": 22,
            "protocol": 1,
            "remote_directory": None,
            "username": "alice",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "comments": None,
            "data_type": "filezilla:site_manager:site",
            "folder_path": "Customers/Production",
            "hostname": "192.0.2.10",
            "logon_type": 2,
            "name": "Customer production",
            "port_number": 21,
            "protocol": 4,
            "username": "deploy",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "filezilla:site_manager:site",
            "folder_path": None,
            "hostname": "198.51.100.20",
            "key_file": "C:\\Users\\labadmin\\.ssh\\lab_dummy_rsa.ppk",
            "logon_type": 5,
            "name": "Key site",
            "port_number": 22,
            "protocol": 1,
            "username": "bob",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "filezilla:site_manager:site",
            "folder_path": None,
            "hostname": "ftp.example.com",
            "logon_type": 0,
            "name": "Public mirror",
            "port_number": 21,
            "protocol": 6,
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # Test that the stored password is not extracted.
        for event_data in storage_writer.GetAttributeContainers("event_data"):
            for _, attribute_value in event_data.GetAttributes():
                self.assertNotIn("DummyPass1", str(attribute_value))
                self.assertNotIn("RHVtbXlQYXNzMQ==", str(attribute_value))

    def testParseWithNameAsServerText(self):
        """Tests the Parse function with the site name stored as Server text."""
        storage_writer = self._ParseData(
            b"".join(
                [
                    b'<?xml version="1.0" encoding="UTF-8"?>\n',
                    b'<FileZilla3 version="3.72.1" platform="windows">\n',
                    b"<Servers><Server><Host>ftp.example.com</Host>",
                    b"<Pass>DummyPass2</Pass>\n",
                    b"Legacy site&#x0A;</Server></Servers>\n",
                    b"</FileZilla3>\n",
                ]
            )
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        expected_event_values = {
            "data_type": "filezilla:site_manager:site",
            "hostname": "ftp.example.com",
            "name": "Legacy site",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        for _, attribute_value in event_data.GetAttributes():
            self.assertNotIn("DummyPass2", str(attribute_value))

    def testParseWithUnsupportedPortNumber(self):
        """Tests the Parse function with an unsupported port number."""
        storage_writer = self._ParseData(
            b"".join(
                [
                    b'<?xml version="1.0" encoding="UTF-8"?>\n',
                    b'<FileZilla3 version="3.72.1" platform="windows">\n',
                    b"<Servers><Server><Host>ftp.example.com</Host>",
                    b"<Port>bogus</Port></Server></Servers>\n",
                    b"</FileZilla3>\n",
                ]
            )
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "data_type": "filezilla:site_manager:site",
            "hostname": "ftp.example.com",
            "port_number": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithOtherXMLFiles(self):
        """Tests the Parse function with XML files of other formats."""
        parser = filezilla.FileZillaSiteManagerParser()

        for filename in (
            "filezilla.xml",
            "filezilla_recentservers.xml",
            "ReAgent.xml",
            "SAFStore.xml",
            "SampleMachineList.xml",
            "typed_history.xml",
            "usage-history.xml",
        ):
            with self.assertRaises(errors.WrongParser):
                self._ParseFile([filename], parser)

    def testParseWithWrongFormat(self):
        """Tests the Parse function with data of the wrong format."""
        # Test with data that is not XML.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(b"<FileZilla3><Servers></Servers></FileZilla3>\n")

        # Test with malformed XML.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(
                b"".join(
                    [
                        b'<?xml version="1.0" encoding="UTF-8"?>\n',
                        b'<FileZilla3 version="3.72.1" platform="windows">\n',
                        b"<Servers><Server><Host>ftp.example.com</Server>\n",
                    ]
                )
            )

        # Test with XML that specifies an unsupported encoding.
        for encoding in (b"bogus", b"big5"):
            with self.assertRaises(errors.WrongParser):
                self._ParseData(
                    b"".join(
                        [
                            b'<?xml version="1.0" encoding="',
                            encoding,
                            b'" ?>\n',
                            b"<FileZilla3><Servers></Servers></FileZilla3>\n",
                        ]
                    )
                )


if __name__ == "__main__":
    unittest.main()
