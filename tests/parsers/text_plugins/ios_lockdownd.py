#!/usr/bin/env python3
"""Tests for the iOS lockdown daemon log files text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import ios_lockdownd

from tests.parsers.text_plugins import test_lib


class IOSLockdowndLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the iOS lockdown daemon log files text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = ios_lockdownd.IOSLockdowndLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"10/13/21 07:57:42.865446 pid=69 mglog: libMobileGestalt "
            b"MGBasebandSupport.c:183: No IMEI in CT mobile equipment info "
            b"dictionary\n"
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
        plugin = ios_lockdownd.IOSLockdowndLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["ios_lockdownd.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 153)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "body": (
                "handle_get_value: AMPDevicesAgent attempting to get "
                "[InternationalMobileSubscriberIdentity2]"
            ),
            "data_type": "ios:lockdownd_log:entry",
            "process_identifier": 69,
            "written_time": "2021-10-13T07:57:42.869324+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "body": (
                "spawn_xpc_service_block_invoke: description of xpc reply: "
                "<dictionary: 0x2029c5070> { count = 1, transaction: 0, "
                'voucher = 0x0, contents = "XPCErrorDescription" => <string: '
                '0x2029c5230> { length = 22, contents = "Connection '
                'interrupted" } }'
            ),
            "data_type": "ios:lockdownd_log:entry",
            "process_identifier": 69,
            "written_time": "2021-10-13T07:57:42.950704+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 99)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
