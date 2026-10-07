#!/usr/bin/env python3
"""Tests for the Microsoft HTTP API (HTTP.sys) error log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import winhttperr

from tests.parsers.text_plugins import test_lib


class WinHTTPErrTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the Microsoft HTTP API (HTTP.sys) error log text parser plugin."""

    _HEADER = (
        b"#Software: Microsoft HTTP API 2.0\r\n"
        b"#Version: 1.0\r\n"
        b"#Date: 2025-03-14 08:00:01\r\n"
    )

    def _ParseData(self, data):
        """Parses data with the plugin.

        Args:
          data (bytes): data of a HTTP.sys error log file.

        Returns:
          FakeStorageWriter: storage writer.
        """
        plugin = winhttperr.WinHTTPErrTextPlugin()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = parsers_mediator.ParserMediator()
        parser_mediator.SetStorageWriter(storage_writer)

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(
            file_object, encoding=plugin.ENCODING
        )
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        plugin.Process(parser_mediator, file_object=file_object)

        return storage_writer

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = winhttperr.WinHTTPErrTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            self._HEADER + b"#Fields: date time c-ip c-port s-ip s-port cs-version "
            b"cs-method cs-uri sc-status s-siteid s-reason s-queuename\r\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check that an IIS log file, which uses the same W3C extended log file
        # format, does not match.
        file_object = io.BytesIO(
            b"#Software: Microsoft Internet Information Services 10.0\r\n"
            b"#Version: 1.0\r\n"
            b"#Date: 2025-03-14 08:00:01\r\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

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
        plugin = winhttperr.WinHTTPErrTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["httperr", "httperr.log"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A requested URI that contains characters used in SQL injection attempts.
        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "dest_ip": "127.0.0.1",
            "dest_port": 8123,
            "extended_fault_code": None,
            "fault_code": None,
            "http_method": "GET",
            "http_status": 400,
            "last_written_time": "2026-10-07T12:24:54+00:00",
            "protocol_version": "HTTP/1.1",
            "queue_name": None,
            "reason": "Hostname",
            "requested_uri": "/test'XOR(1)*!",
            "site_identifier": None,
            "source_ip": "127.0.0.1",
            "source_port": 54517,
            "stream_identifier": None,
            "transport": "TCP",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A request rejected before the method, URI and version could be parsed.
        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "http_method": None,
            "http_status": 400,
            "last_written_time": "2026-10-07T12:24:55+00:00",
            "protocol_version": None,
            "reason": "Verb",
            "requested_uri": None,
            "source_port": 54519,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithServiceRestart(self):
        """Tests the Process function with fields that change within the file."""
        plugin = winhttperr.WinHTTPErrTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["httperr", "httperr_restart.log"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Entry from the first block with the HTTP API 2.0 default fields.
        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "http_status": None,
            "last_written_time": "2025-03-14T08:02:15+00:00",
            "reason": "Timer_ConnectionIdle",
            "requested_uri": None,
            "source_ip": "192.0.2.11",
            "transport": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Requested URI with characters that are not valid in an URI.
        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "requested_uri": "/(select+198766*667891)/index.js#frag{}|^~[]`<>@$",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # Entry from the second block, after the HTTP service was restarted, with
        # an IPv6 address with a zone index.
        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "dest_ip": "2001:db8::1",
            "http_method": "POST",
            "http_status": 413,
            "last_written_time": "2025-03-14T09:15:02+00:00",
            "protocol_version": "HTTP/2.0",
            "queue_name": "MyAppPool",
            "reason": "Request_Too_Large",
            "site_identifier": 2,
            "source_ip": "2001:db8::5%12",
            "stream_identifier": "3",
            "transport": "TCP",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "extended_fault_code": "0x1",
            "fault_code": "0x80070008",
            "reason": "QueueFull",
            "transport": "QUIC",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithoutFields(self):
        """Tests the Process function without a fields definition."""
        storage_writer = self._ParseData(
            self._HEADER + b"2025-03-14 08:00:01 192.0.2.10 50123 192.0.2.1 80 "
            b"HTTP/1.1 GET /default.aspx 503 1 AppOffline DefaultAppPool\r\n"
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "http_status": 503,
            "queue_name": "DefaultAppPool",
            "reason": "AppOffline",
            "requested_uri": "/default.aspx",
            "site_identifier": 1,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithUnsupportedField(self):
        """Tests the Process function with an unsupported field."""
        storage_writer = self._ParseData(
            self._HEADER + b"#Fields: date time c-ip s-reason x-custom\r\n"
            b"2025-03-14 08:00:01 192.0.2.10 Hostname custom-value\r\n"
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        warning = storage_writer.GetAttributeContainerByIndex("extraction_warning", 0)
        self.assertIn("missing definition for field: x-custom", warning.message)

        expected_event_values = {
            "data_type": "windows:httperr_log:entry",
            "reason": "Hostname",
            "source_ip": "192.0.2.10",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithInvalidDate(self):
        """Tests the Process function with an invalid date."""
        storage_writer = self._ParseData(
            self._HEADER + b"#Fields: date time c-ip s-reason\r\n"
            b"2025-13-14 08:00:01 192.0.2.10 Hostname\r\n"
            b"2025-03-14 08:00:02 192.0.2.11 Hostname\r\n"
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        warning = storage_writer.GetAttributeContainerByIndex("extraction_warning", 0)
        self.assertIn("Unable to parse time elements", warning.message)


if __name__ == "__main__":
    unittest.main()
