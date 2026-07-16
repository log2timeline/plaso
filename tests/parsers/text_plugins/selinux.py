#!/usr/bin/env python3
"""Tests for the selinux log file text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import selinux

from tests.parsers.text_plugins import test_lib


class SELinuxTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the selinux log file text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = selinux.SELinuxTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"type=LOGIN msg=audit(1337845201.174:94983): pid=25443 uid=0 "
            b"old auid=4294967295 new auid=0 old ses=4294967295 new ses=1165\n"
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
        plugin = selinux.SELinuxTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["selinux.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 7)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test case: normal entry.
        expected_event_values = {
            "audit_serial": 94983,
            "audit_type": "LOGIN",
            "data_type": "selinux:line",
            "message_body": (
                "pid=25443 uid=0 old auid=4294967295 new auid=0 old ses=4294967295 "
                "new ses=1165"
            ),
            "last_written_time": "2012-05-24T07:40:01.174+00:00",
            "pid": "25443",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test case: short date.
        expected_event_values = {
            "audit_type": "SHORTDATE",
            "data_type": "selinux:line",
            "message_body": "check rounding",
            "last_written_time": "2012-05-24T07:40:01.000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Test case: no message.
        expected_event_values = {
            "audit_type": "NOMSG",
            "data_type": "selinux:line",
            "last_written_time": "2012-05-24T07:40:22.174+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # Test case: under score.
        expected_event_values = {
            "audit_type": "UNDER_SCORE",
            "data_type": "selinux:line",
            "message_body": (
                "pid=25444 uid=0 old auid=4294967295 new auid=54321 old "
                "ses=4294967295 new ses=1166"
            ),
            "last_written_time": "2012-05-24T07:47:46.174+00:00",
            "pid": "25444",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # Test case: SYSCALL record - Tier 1 structured fields.
        expected_event_values = {
            "audit_login_identifier": "0",
            "audit_serial": 101,
            "audit_session_identifier": "1",
            "audit_type": "SYSCALL",
            "data_type": "selinux:line",
            "executable": "/bin/ls",
            "exit_code": "0",
            "group_identifier": "0",
            "parent_process_identifier": "2671",
            "pid": "2714",
            "process_name": "ls",
            "security_context": "system_u:object_r:unlabeled_t:s0",
            "success": "yes",
            "system_call": "197",
            "user_identifier": "0",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessEnriched(self):
        """Tests the Process function on an ENRICHED (0x1d-suffixed) audit log."""
        plugin = selinux.SELinuxTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["audit_enriched.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 29)

        # A SYSCALL execve record (serial 485): the raw "syscall=59" is surfaced as
        # the ENRICHED "SYSCALL=execve" name, and the 0x1d suffix is split off.
        expected_event_values = {
            "audit_login_identifier": "0",
            "audit_serial": 485,
            "audit_session_identifier": "8",
            "audit_type": "SYSCALL",
            "data_type": "selinux:line",
            "executable": "/usr/bin/id",
            "exit_code": "0",
            "group_identifier": "0",
            "parent_process_identifier": "2176",
            "pid": "2219",
            "process_name": "id",
            "security_context": (
                "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023"
            ),
            "success": "yes",
            "system_call": "execve",
            "user_identifier": "0",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 11)
        self.CheckEventData(event_data, expected_event_values)

        # The ENRICHED suffix (after the 0x1d separator) is not retained.
        self.assertNotIn("\x1d", event_data.message_body)


if __name__ == "__main__":
    unittest.main()
