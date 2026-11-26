#!/usr/bin/env python3
"""Tests for the Apache Hadoop YARN ResourceManager audit log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import yarn_rm_audit

from tests.parsers.text_plugins import test_lib


class YARNResourceManagerAuditLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the YARN ResourceManager audit log text parser plugin."""

    def _CheckRequiredFormat(self, data):
        """Checks if data has the format required by the plugin.

        Args:
          data (bytes): data of a log file.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        plugin = yarn_rm_audit.YARNResourceManagerAuditLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        result = self._CheckRequiredFormat(
            b"2026-11-26 11:15:43,731 INFO resourcemanager.RMAuditLogger: "
            b"USER=alice\tIP=127.0.0.1\tOPERATION=Submit Application Request\t"
            b"TARGET=ClientRMService\tRESULT=SUCCESS\n"
        )
        self.assertTrue(result)

        result = self._CheckRequiredFormat(
            b"2026-11-26 11:31:31,261 WARN resourcemanager.RMAuditLogger: "
            b"USER=bob\tIP=127.0.0.1\tOPERATION=refreshQueues\t"
            b"TARGET=AdminService\tRESULT=FAILURE\tDESCRIPTION=Unauthorized "
            b"user\tPERMISSIONS=\n"
        )
        self.assertTrue(result)

        # Check that a YARN ResourceManager application summary log line does
        # not match.
        result = self._CheckRequiredFormat(
            b"2026-11-26 11:16:41,938 INFO resourcemanager.RMAppManager"
            b"$ApplicationSummary: appId=application_1795691698555_0001,"
            b"name=QuasiMonteCarlo,user=alice,queue=root.default\n"
        )
        self.assertFalse(result)

        # Check that a log line with an invalid date does not match.
        result = self._CheckRequiredFormat(
            b"2026-02-30 11:15:43,731 INFO resourcemanager.RMAuditLogger: "
            b"USER=alice\tIP=127.0.0.1\tOPERATION=Submit Application Request\t"
            b"TARGET=ClientRMService\tRESULT=SUCCESS\n"
        )
        self.assertFalse(result)

        # Check that an Atlassian Jira log line does not match.
        result = self._CheckRequiredFormat(
            b"2022-10-03 09:00:01,042 INFO [main] [com.atlassian.jira.startup."
            b"JiraStartupLogger] start Jira starting...\n"
        )
        self.assertFalse(result)

        # Check non-matching format.
        result = self._CheckRequiredFormat(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        self.assertFalse(result)

    def testCheckRequiredFormatWithOtherTextFile(self):
        """Tests for the CheckRequiredFormat function with another text file."""
        test_file_path = self._GetTestFilePath(["atlassian-jira.log"])
        self._SkipIfPathNotExists(test_file_path)

        with open(test_file_path, "rb") as file_object:
            data = file_object.read()

        result = self._CheckRequiredFormat(data)
        self.assertFalse(result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = yarn_rm_audit.YARNResourceManagerAuditLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["yarn_rm_audit.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 20)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A submit application request.
        expected_event_values = {
            "application_identifier": "application_1795691698555_0001",
            "attempt_identifier": None,
            "caller_context": "CLI",
            "caller_signature": None,
            "container_identifier": None,
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "description": None,
            "include_applications": None,
            "include_child_queues": None,
            "ip_address": "127.0.0.1",
            "node_label": None,
            "operation": "Submit Application Request",
            "permissions": None,
            "queue": "default",
            "recursive": None,
            "resource": None,
            "result": "SUCCESS",
            "target": "ClientRMService",
            "user": "alice",
            "written_time": "2026-11-26T11:15:43.731",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A container allocation.
        expected_event_values = {
            "application_identifier": "application_1795691698555_0001",
            "container_identifier": "container_1795691698555_0001_01_000001",
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "ip_address": None,
            "operation": "AM Allocated Container",
            "queue": "default",
            "resource": "<memory:512, vCores:1>",
            "result": "SUCCESS",
            "target": "SchedulerApp",
            "user": "alice",
            "written_time": "2026-11-26T11:15:46.461",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # A denied kill application request.
        expected_event_values = {
            "application_identifier": "application_1795691698555_0003",
            "caller_context": "CLI",
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "description": "Unauthorized user",
            "ip_address": "127.0.0.1",
            "operation": "Kill Application Request",
            "permissions": "User doesn't have permissions to MODIFY_APP",
            "result": "FAILURE",
            "target": "ClientRMService",
            "user": "bob",
            "written_time": "2026-11-26T11:29:48.931",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 10)
        self.CheckEventData(event_data, expected_event_values)

        # A get queue information request.
        expected_event_values = {
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "include_applications": "true",
            "include_child_queues": "false",
            "operation": "Get Queue Info Request",
            "queue": "default",
            "recursive": "false",
            "user": "bob",
            "written_time": "2026-11-26T11:31:26.125",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 17)
        self.CheckEventData(event_data, expected_event_values)

        # A denied refresh queues request without permissions.
        expected_event_values = {
            "application_identifier": None,
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "description": "Unauthorized user",
            "operation": "refreshQueues",
            "permissions": None,
            "result": "FAILURE",
            "target": "AdminService",
            "user": "bob",
            "written_time": "2026-11-26T11:31:31.261",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18)
        self.CheckEventData(event_data, expected_event_values)

        # The last log line.
        expected_event_values = {
            "application_identifier": None,
            "attempt_identifier": None,
            "caller_context": None,
            "caller_signature": None,
            "container_identifier": None,
            "data_type": "hadoop:yarn:resourcemanager:audit",
            "description": None,
            "include_applications": None,
            "include_child_queues": None,
            "ip_address": "127.0.0.1",
            "node_label": None,
            "operation": "refreshQueues",
            "permissions": None,
            "queue": None,
            "recursive": None,
            "resource": None,
            "result": "SUCCESS",
            "target": "AdminService",
            "user": "hadoop",
            "written_time": "2026-11-26T11:31:36.052",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 19)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
