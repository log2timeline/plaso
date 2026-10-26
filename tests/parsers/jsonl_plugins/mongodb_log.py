#!/usr/bin/env python3
"""Tests for the JSON-L parser plugin for MongoDB log files."""

import unittest

from plaso.parsers.jsonl_plugins import mongodb_log

from tests.parsers.jsonl_plugins import test_lib


class MongoDBLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
    """Tests for the JSON-L parser plugin for MongoDB log files."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = mongodb_log.MongoDBLogJSONLPlugin()

        json_dict = {
            "t": {"$date": "2025-10-07T11:02:13.640+02:00"},
            "s": "I",
            "c": "NETWORK",
            "id": 22944,
            "ctx": "conn12",
            "msg": "Connection ended",
        }
        self.assertTrue(plugin.CheckRequiredFormat(json_dict))

        # Check that a record with an invalid date and time value does not match.
        json_dict = {
            "t": {"$date": "2025-10-07 11:02"},
            "s": "I",
            "c": "NETWORK",
            "id": 22944,
            "msg": "Connection ended",
        }
        self.assertFalse(plugin.CheckRequiredFormat(json_dict))

        # Check that a record with the date and time value not stored in "$date"
        # does not match.
        json_dict = {
            "t": "2025-10-07T11:02:13.640+02:00",
            "s": "I",
            "c": "NETWORK",
            "id": 22944,
            "msg": "Connection ended",
        }
        self.assertFalse(plugin.CheckRequiredFormat(json_dict))

        # Check that a record without a message identifier does not match.
        json_dict = {
            "t": {"$date": "2025-10-07T11:02:13.640+02:00"},
            "s": "I",
            "c": "NETWORK",
            "msg": "Connection ended",
        }
        self.assertFalse(plugin.CheckRequiredFormat(json_dict))

        # Check that a Docker container log record does not match.
        json_dict = {
            "log": "Connection ended\n",
            "stream": "stdout",
            "time": "2025-10-07T09:02:13.640000000Z",
        }
        self.assertFalse(plugin.CheckRequiredFormat(json_dict))

        # Check that a Google Cloud log record does not match.
        json_dict = {
            "logName": "projects/example/logs/syslog",
            "severity": "INFO",
            "textPayload": "Connection ended",
            "timestamp": "2025-10-07T09:02:13.640Z",
        }
        self.assertFalse(plugin.CheckRequiredFormat(json_dict))

    def testProcess(self):
        """Tests the Process function."""
        plugin = mongodb_log.MongoDBLogJSONLPlugin()
        storage_writer = self._ParseJSONLFileWithPlugin(
            ["jsonl", "mongodb.jsonl"], plugin
        )

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

        # A record without attributes.
        expected_event_values = {
            "attributes": None,
            "component": "CONTROL",
            "context": "main",
            "data_type": "mongodb:log:entry",
            "message_body": "***** SERVER RESTARTED *****",
            "message_identifier": 20698,
            "recorded_time": "2025-10-06T09:15:02.104000+00:00",
            "severity": "I",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A record with attributes that are not strings.
        expected_event_values = {
            "attributes": ["port: 27017", "ssl: off"],
            "component": "NETWORK",
            "context": "listener",
            "data_type": "mongodb:log:entry",
            "message_body": "Waiting for connections",
            "message_identifier": 23016,
            "recorded_time": "2025-10-06T09:15:03.551000+00:00",
            "severity": "I",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # A record with nested attributes.
        expected_event_values = {
            "attributes": [
                "type: command",
                "ns: inventory.items",
                'command: {"find":"items","filter":{"sku":"A-100"}}',
                "durationMillis: 214",
            ],
            "data_type": "mongodb:log:entry",
            "message_body": "Slow query",
            "severity": "W",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
