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

    # pylint: disable=protected-access

    def testDecodeHexValueOddLength(self):
        """Tests that an odd-length hex value is preserved, not decoded."""
        plugin = selinux.SELinuxTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        # An odd-length token is not valid hex-encoded data and must be
        # returned as a literal rather than raising ValueError, which would
        # crash extraction on a single malformed record.
        self.assertEqual(plugin._DecodeHexValue(parser_mediator, "abc"), "abc")

        # A well-formed even-length value still decodes byte-preservingly.
        self.assertEqual(plugin._DecodeHexValue(parser_mediator, "6162"), "ab")

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

    def _FindEventDataByTypeAndSerial(self, storage_writer, audit_type, serial):
        """Returns the first event data with the given audit type and serial."""
        for event_data in storage_writer.GetAttributeContainers("event_data"):
            if event_data.audit_type == audit_type and (
                event_data.audit_serial == serial
            ):
                return event_data
        self.fail(f"no {audit_type:s} event with serial {serial:d}")

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

        # SYSCALL (serial 485): ENRICHED ARCH resolves the architecture name.
        expected_event_values = {
            "audit_type": "SYSCALL",
            "architecture": "x86_64",
            "system_call": "execve",
            "audit_rule_key": "specimen_exec",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "SYSCALL", 485)
        self.CheckEventData(event_data, expected_event_values)

        # EXECVE (serial 487): hex-encoded final argument decoded, space-joined.
        expected_event_values = {
            "audit_type": "EXECVE",
            "arguments": "/bin/sh -c grep -c . /etc/hostname",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "EXECVE", 487)
        self.CheckEventData(event_data, expected_event_values)

        # USER_AUTH (serial 441): a failed remote pubkey auth from addr.
        expected_event_values = {
            "audit_type": "USER_AUTH",
            "operation": "pubkey",
            "result": "failed",
            "remote_address": "172.23.112.1",
        }
        event_data = self._FindEventDataByTypeAndSerial(
            storage_writer, "USER_AUTH", 441
        )
        self.CheckEventData(event_data, expected_event_values)

        # USER_ACCT (serial 444): a remote auth event with a resolved hostname,
        # address and terminal (exercises remote_hostname with a real value).
        expected_event_values = {
            "audit_type": "USER_ACCT",
            "account": "root",
            "operation": "PAM:accounting",
            "remote_address": "172.23.112.1",
            "remote_hostname": "172.23.112.1",
            "result": "success",
            "terminal": "ssh",
        }
        event_data = self._FindEventDataByTypeAndSerial(
            storage_writer, "USER_ACCT", 444
        )
        self.CheckEventData(event_data, expected_event_values)

    def testProcessAudit(self):
        """Tests the Process function on a RAW auditd audit.log."""
        plugin = selinux.SELinuxTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["audit.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 34)

        # EXECVE with a hex-encoded argument (serial 505): a0="/bin/cat" is
        # literal, a1 is hex-encoded and decoded byte-preserving, space-joined.
        expected_event_values = {
            "audit_serial": 505,
            "audit_type": "EXECVE",
            "arguments": "/bin/cat /tmp/my report.txt",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "EXECVE", 505)
        self.CheckEventData(event_data, expected_event_values)

        # PROCTITLE hex blob (serial 522): NUL separators rendered as spaces.
        expected_event_values = {
            "audit_type": "PROCTITLE",
            "proctitle": "/usr/sbin/unix_chkpwd specimenuser chkexpiry",
        }
        event_data = self._FindEventDataByTypeAndSerial(
            storage_writer, "PROCTITLE", 522
        )
        self.CheckEventData(event_data, expected_event_values)

        # PATH file_path (serial 522, item 0): a quoted name is literal.
        expected_event_values = {
            "audit_type": "PATH",
            "file_path": "/etc/shadow",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "PATH", 522)
        self.CheckEventData(event_data, expected_event_values)

        # SYSCALL (serial 500): raw arch retained (RAW log, no ENRICHED suffix),
        # audit rule key surfaced, key=(null) would map to None.
        expected_event_values = {
            "audit_type": "SYSCALL",
            "architecture": "c000003e",
            "audit_rule_key": "specimen_exec",
            "system_call": "59",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "SYSCALL", 500)
        self.CheckEventData(event_data, expected_event_values)

        # CWD (serial 500): working directory.
        expected_event_values = {
            "audit_type": "CWD",
            "working_directory": "/home/ubuntu",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "CWD", 500)
        self.CheckEventData(event_data, expected_event_values)

        # PATH file metadata (serial 522, item 0 = /etc/shadow).
        expected_event_values = {
            "audit_type": "PATH",
            "file_mode": "0100640",
            "owner_user_identifier": "0",
            "owner_group_identifier": "42",
            "name_type": "NORMAL",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "PATH", 522)
        self.CheckEventData(event_data, expected_event_values)

        # USER_AUTH (serial 520): nested msg='…' fields. terminal/addr/hostname
        # are the "?" sentinel here and map to None.
        expected_event_values = {
            "audit_type": "USER_AUTH",
            "account": "specimenuser",
            "operation": "PAM:authentication",
            "result": "success",
            "terminal": None,
            "remote_address": None,
        }
        event_data = self._FindEventDataByTypeAndSerial(
            storage_writer, "USER_AUTH", 520
        )
        self.CheckEventData(event_data, expected_event_values)

        # DEL_USER (serial 508): a failed operation.
        expected_event_values = {
            "audit_type": "DEL_USER",
            "account": "specimenuser",
            "result": "failed",
        }
        event_data = self._FindEventDataByTypeAndSerial(storage_writer, "DEL_USER", 508)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
