#!/usr/bin/env python3
"""Tests for the Apache error log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import apache_error

from tests.parsers.text_plugins import test_lib


class ApacheErrorLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the Apache error log text parser plugin."""

    def _CheckRequiredFormat(self, data):
        """Checks if data has the format required by the plugin.

        Args:
          data (bytes): data of a log file.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        plugin = apache_error.ApacheErrorLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        result = self._CheckRequiredFormat(
            b"[Tue Oct 07 11:02:13.640057 2025] [core:error] [pid 2310:tid 2402] "
            b"[client 192.0.2.5:40112] AH00037: Symbolic link not allowed\n"
        )
        self.assertTrue(result)

        # Check a log line without a module name and a thread identifier.
        result = self._CheckRequiredFormat(
            b"[Tue Oct 07 11:02:13.640057 2025] [:error] [pid 2310] PHP Notice\n"
        )
        self.assertTrue(result)

        # Check that an Apache access log line does not match.
        result = self._CheckRequiredFormat(
            b'192.0.2.5 - - [07/Oct/2025:11:02:13 +0200] "GET / HTTP/1.1" 200 512\n'
        )
        self.assertFalse(result)

        # Check that an Apache 2.2 error log line, without module name, process
        # identifier and sub-second precision, does not match.
        result = self._CheckRequiredFormat(
            b"[Tue Oct 07 11:02:13 2025] [error] [client 192.0.2.5] File does not "
            b"exist: /var/www/favicon.ico\n"
        )
        self.assertFalse(result)

        # Check that a log line with an unsupported severity level does not match.
        result = self._CheckRequiredFormat(
            b"[Tue Oct 07 11:02:13.640057 2025] [core:fatal] [pid 2310] Failure\n"
        )
        self.assertFalse(result)

        # Check that a log line with an invalid date does not match.
        result = self._CheckRequiredFormat(
            b"[Thu Feb 30 11:02:13.640057 2025] [core:error] [pid 2310] Failure\n"
        )
        self.assertFalse(result)

        # Check non-matching format.
        result = self._CheckRequiredFormat(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        self.assertFalse(result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = apache_error.ApacheErrorLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["apache_error.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 7)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A log line without a client address.
        expected_event_values = {
            "client_address": None,
            "data_type": "apache:error_log:entry",
            "level": "notice",
            "message_body": (
                "AH00489: Apache/2.4.62 (Debian) configured -- resuming normal "
                "operations"
            ),
            "module": "mpm_event",
            "process_identifier": 1021,
            "recorded_time": "2025-10-06T09:15:02.104311",
            "thread_identifier": 1021,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A log line with a client address.
        expected_event_values = {
            "client_address": "198.51.100.4:61022",
            "data_type": "apache:error_log:entry",
            "level": "error",
            "message_body": (
                "AH01630: client denied by server configuration: /var/www/html/admin"
            ),
            "module": "authz_core",
            "process_identifier": 1188,
            "recorded_time": "2025-10-06T09:18:10.000412",
            "thread_identifier": 1206,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # A log line without a module name and thread identifier.
        expected_event_values = {
            "client_address": "203.0.113.80:44310",
            "data_type": "apache:error_log:entry",
            "level": "error",
            "module": None,
            "process_identifier": 1190,
            "recorded_time": "2025-10-06T09:20:31.774900",
            "thread_identifier": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
