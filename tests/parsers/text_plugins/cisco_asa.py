#!/usr/bin/env python3
"""Tests for the Cisco ASA log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import cisco_asa

from tests.parsers.text_plugins import test_lib


class CiscoASALogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the Cisco ASA log text parser plugin."""

    def _CheckRequiredFormat(self, data):
        """Checks if data has the format required by the plugin.

        Args:
          data (bytes): data of a log file.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        plugin = cisco_asa.CiscoASALogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        result = self._CheckRequiredFormat(
            b"2022-01-01T00:01:27+01:00 asa5540-2 : %ASA-5-722037: Group "
            b"<DfltGrpPolicy> User <user> IP <192.0.2.1> SVC closing connection: "
            b"DPD failure.\n"
        )
        self.assertTrue(result)

        # Check a log line with fractional seconds and an UTC time zone.
        result = self._CheckRequiredFormat(
            b"2022-01-01T00:01:27.123Z asa5540-2 : %ASA-6-302013: Built inbound "
            b"TCP connection\n"
        )
        self.assertTrue(result)

        # Check that a rsyslog line without an ASA message identifier does not
        # match.
        result = self._CheckRequiredFormat(
            b"2020-05-31T00:00:45.698463+00:00 hostname rsyslogd: [origin "
            b'software="rsyslogd"] rsyslogd was HUPed\n'
        )
        self.assertFalse(result)

        # Check that a log line with an unsupported severity level does not match.
        result = self._CheckRequiredFormat(
            b"2022-01-01T00:01:27+01:00 asa5540-2 : %ASA-8-722037: Group "
            b"<DfltGrpPolicy> SVC closing connection\n"
        )
        self.assertFalse(result)

        # Check that a log line with an invalid date does not match.
        result = self._CheckRequiredFormat(
            b"2022-02-30T00:01:27+01:00 asa5540-2 : %ASA-5-722037: Group "
            b"<DfltGrpPolicy> SVC closing connection\n"
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
        plugin = cisco_asa.CiscoASALogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["cisco_asa.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "cisco:asa:log:entry",
            "hostname": "asa5540-2",
            "message_body": (
                "Group <DfltGrpPolicy> User <testuser0> IP <192.0.2.10> SVC closing "
                "connection: DPD failure."
            ),
            "message_identifier": 722037,
            "recorded_time": "2022-01-01T00:01:27+01:00",
            "severity": 5,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "cisco:asa:log:entry",
            "hostname": "asa5540-2",
            "message_body": (
                "Group = DefaultWEBVPNGroup, Username = admin, IP = 192.0.2.20, "
                "Session disconnected. Session Type: SSL, Duration: 2h:10m:54s, "
                "Bytes xmt: 24693444, Bytes rcv: 6056715, Reason: Idle Timeout"
            ),
            "message_identifier": 113019,
            "recorded_time": "2022-01-01T00:02:43+01:00",
            "severity": 4,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "cisco:asa:log:entry",
            "hostname": "asa5540-1",
            "message_identifier": 722033,
            "recorded_time": "2022-01-01T00:03:51+01:00",
            "severity": 5,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
