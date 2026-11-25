#!/usr/bin/env python3
"""Tests for the Squid access log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import squid_access

from tests.parsers.text_plugins import test_lib


class SquidAccessLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the Squid access log text parser plugin."""

    def _CheckRequiredFormat(self, data):
        """Checks if data has the format required by the plugin.

        Args:
          data (bytes): data of a log file.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        plugin = squid_access.SquidAccessLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        result = self._CheckRequiredFormat(
            b"1759742102.104    187 192.0.2.17 TCP_MISS/200 10341 GET "
            b"http://www.example.com/ - HIER_DIRECT/198.51.100.10 text/html\n"
        )
        self.assertTrue(result)

        # Check that a log line in the Apache (httpd) emulation log format does
        # not match.
        result = self._CheckRequiredFormat(
            b"192.0.2.17 - - [06/Oct/2025:09:15:02 +0000] "
            b'"GET http://www.example.com/ HTTP/1.1" 200 10341 TCP_MISS:HIER_DIRECT\n'
        )
        self.assertFalse(result)

        # Check that a log line with a timestamp without milliseconds does not
        # match.
        result = self._CheckRequiredFormat(
            b"1759742102    187 192.0.2.17 TCP_MISS/200 10341 GET "
            b"http://www.example.com/ - HIER_DIRECT/198.51.100.10 text/html\n"
        )
        self.assertFalse(result)

        # Check that a log line without the hierarchy code does not match.
        result = self._CheckRequiredFormat(
            b"1759742102.104    187 192.0.2.17 TCP_MISS/200 10341 GET "
            b"http://www.example.com/ - text/html\n"
        )
        self.assertFalse(result)

        # Check non-matching format.
        result = self._CheckRequiredFormat(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        self.assertFalse(result)

    def testProcessWithErrorLines(self):
        """Tests the Process function with log lines of failed requests."""
        plugin = squid_access.SquidAccessLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["squid_access_errors.log"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Note that the request method of a request that failed before the method
        # was received is "-".
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.cache_result, "NONE_NONE")
        self.assertEqual(event_data.http_response_code, 0)
        self.assertIsNone(event_data.http_request_method)
        self.assertEqual(event_data.url, "error:transaction-end-before-headers")

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.assertEqual(event_data.http_request_method, "NONE")

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.assertEqual(event_data.cache_result, "TCP_MISS_ABORTED")
        self.assertEqual(event_data.http_request_method, "GET")

    def testProcessWithSquid7Log(self):
        """Tests the Process function with a log written by Squid 7.7."""
        plugin = squid_access.SquidAccessLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["squid_access_squid77.log"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A request that Squid rejected as malformed is logged without a method.
        expected_event_values = {
            "cache_result": "NONE_NONE",
            "client_address": "127.0.0.1",
            "data_type": "squid:access_log:entry",
            "http_request_method": None,
            "http_response_code": 400,
            "recorded_time": "2026-11-14T11:48:18.621+00:00",
            "url": "/",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

    def testProcess(self):
        """Tests the Process function."""
        plugin = squid_access.SquidAccessLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["squid_access.log"], plugin)

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

        # A CONNECT request without a content type.
        expected_event_values = {
            "cache_result": "TCP_TUNNEL",
            "client_address": "192.0.2.17",
            "content_type": None,
            "data_type": "squid:access_log:entry",
            "elapsed_time": 60125,
            "hierarchy_code": "HIER_DIRECT",
            "http_request_method": "CONNECT",
            "http_response_code": 200,
            "peer_host": "198.51.100.11",
            "recorded_time": "2025-10-06T09:16:04.551+00:00",
            "response_size": 5822,
            "url": "www.example.org:443",
            "username": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # A denied request without a peer host.
        expected_event_values = {
            "cache_result": "TCP_DENIED",
            "data_type": "squid:access_log:entry",
            "elapsed_time": 0,
            "hierarchy_code": "HIER_NONE",
            "http_response_code": 403,
            "peer_host": None,
            "recorded_time": "2025-10-06T09:18:10.000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # A request with a user name and IPv6 addresses.
        expected_event_values = {
            "client_address": "2001:db8::25",
            "content_type": "text/css",
            "data_type": "squid:access_log:entry",
            "http_response_code": 304,
            "peer_host": "2001:db8::80",
            "username": "bob",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
