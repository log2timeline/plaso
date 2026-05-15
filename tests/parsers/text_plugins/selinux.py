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
            "audit_type": "LOGIN",
            "body": (
                "pid=25443 uid=0 old auid=4294967295 new auid=0 old ses=4294967295 "
                "new ses=1165"
            ),
            "data_type": "selinux:line",
            "last_written_time": "2012-05-24T07:40:01.174+00:00",
            "pid": "25443",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test case: short date.
        expected_event_values = {
            "audit_type": "SHORTDATE",
            "body": "check rounding",
            "data_type": "selinux:line",
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
            "body": (
                "pid=25444 uid=0 old auid=4294967295 new auid=54321 old "
                "ses=4294967295 new ses=1166"
            ),
            "data_type": "selinux:line",
            "last_written_time": "2012-05-24T07:47:46.174+00:00",
            "pid": "25444",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
