#!/usr/bin/env python3
"""Tests for the vsftpd log file text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import vsftpd

from tests.parsers.text_plugins import test_lib


class VsftpdLogTextPluginText(test_lib.TextPluginTestCase):
    """Tests for the vsftpd log file text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = vsftpd.VsftpdLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b'Mon Jun  6 18:43:28 2016 [pid 2] CONNECT: Client "192.168.1.9"\n'
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_object = io.BytesIO(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process function."""
        plugin = vsftpd.VsftpdLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["vsftpd.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 25)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2016-06-10T14:24:19",
            "data_type": "vsftpd:log",
            "process_identifier": 3,
            "text": (
                'OK DOWNLOAD: Client "192.168.1.7", '
                '"/home/jean/trains/how-thomas-the-tank-engine-works-1.jpg", '
                "49283 bytes, 931.38Kbyte/sec"
            ),
            "username": "jean",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 12)
        self.CheckEventData(event_data, expected_event_values)

        # Log line without username.
        expected_event_values = {
            "added_time": "2016-06-10T14:28:50",
            "data_type": "vsftpd:log",
            "process_identifier": 2,
            "text": 'CONNECT: Client "192.168.1.5"',
            "username": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 13)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithTransferLog(self):
        """Tests the Process function with a transfer log (xferlog) file."""
        plugin = vsftpd.VsftpdLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["vsftpd_xferlog.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access_mode": "r",
            "added_time": "2016-06-06T18:43:59",
            "authenticated_user_identifier": "*",
            "authentication_method": "0",
            "completion_status": "c",
            "data_type": "vsftpd:xferlog",
            "direction": "i",
            "file_size": 1884648,
            "filename": "/home/jean/trains/Caitlinpromo2.png",
            "remote_host": "192.168.1.9",
            "service_name": "ftp",
            "special_action_flag": "_",
            "transfer_duration": 1,
            "transfer_type": "b",
            "username": "jean",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Filename that contains spaces.
        expected_event_values = {
            "data_type": "vsftpd:xferlog",
            "direction": "o",
            "file_size": 40120,
            "filename": "/home/jean/my trains/a b.jpg",
            "transfer_duration": 0,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Incomplete anonymous transfer.
        expected_event_values = {
            "access_mode": "a",
            "completion_status": "i",
            "data_type": "vsftpd:xferlog",
            "transfer_type": "a",
            "username": "n",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # Lines that resemble but do not match the transfer log format, with an
        # unsupported transfer type and with trailing data.
        expected_event_values = {
            "data_type": "vsftpd:log",
            "process_identifier": None,
            "text": "3 192.168.1.5 1024 /photos/cat.txt x _ i a n ftp 0 * i",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "vsftpd:log",
            "text": "3 192.168.1.5 1024 /photos/cat.txt b _ i r jean ftp 0 * c extra",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # Line that resembles but does not match the process log format.
        expected_event_values = {
            "data_type": "vsftpd:log",
            "process_identifier": None,
            "text": '[pid x] CONNECT: Client "192.168.1.5"',
            "username": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
