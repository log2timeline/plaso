#!/usr/bin/env python3
"""Tests for the Samba log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import samba

from tests.parsers.text_plugins import test_lib


class SambaLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the Samba log text parser plugin."""

    def _CheckRequiredFormat(self, data):
        """Checks if data has the format required by the plugin.

        Args:
          data (bytes): data of a log file.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        plugin = samba.SambaLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        result = self._CheckRequiredFormat(
            b"[2025/10/07 11:02:13.640057,  1, pid=2310] "
            b"../../source3/smbd/service.c:1124(make_connection_snum)\n"
            b"  WS01 (ipv4:192.0.2.5:40112) connect to service data\n"
        )
        self.assertTrue(result)

        # Check that an Apache error log line does not match.
        result = self._CheckRequiredFormat(
            b"[Tue Oct 07 11:02:13.640057 2025] [core:error] [pid 2310] "
            b"AH00037: Symbolic link not allowed\n"
        )
        self.assertFalse(result)

        # Check that a header without a source location does not match.
        result = self._CheckRequiredFormat(
            b"[2025/10/07 11:02:13.640057,  1, pid=2310] connect to service data\n"
        )
        self.assertFalse(result)

        # Check that a header with an invalid date does not match.
        result = self._CheckRequiredFormat(
            b"[2025/02/30 11:02:13.640057,  1] "
            b"../../source3/smbd/service.c:1124(make_connection_snum)\n"
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
        plugin = samba.SambaLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["samba.log"], plugin)

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

        # A log entry without process identifier and with multiple message lines.
        expected_event_values = {
            "data_type": "samba:log:entry",
            "debug_class": None,
            "debug_level": 0,
            "function_name": "main",
            "message_body": (
                "smbd version 4.19.5 started.\n"
                "configuration loaded from /etc/samba/smb.conf"
            ),
            "process_identifier": None,
            "recorded_time": "2025-10-06T09:15:02.104311",
            "source_file": "../../source3/smbd/server.c",
            "source_line": 1741,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A log entry with process identifier, user identifiers and debug class.
        expected_event_values = {
            "data_type": "samba:log:entry",
            "debug_class": "auth_audit",
            "debug_level": 2,
            "function_name": "log_authentication_event_human_readable",
            "process_identifier": 1190,
            "recorded_time": "2025-10-06T09:18:10.000412",
            "source_file": "../../auth/auth_log.c",
            "source_line": 635,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # A log entry without fraction of second.
        expected_event_values = {
            "data_type": "samba:log:entry",
            "debug_level": 0,
            "message_body": "daemon_status: daemon 'smbd' : Shutting down",
            "recorded_time": "2025-10-06T09:25:58",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
