#!/usr/bin/env python3
"""Tests for the VMware ESXi log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import esxi

from tests.parsers.text_plugins import test_lib


class ESXiLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the VMware ESXi log text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests the CheckRequiredFormat method."""
        plugin = esxi.ESXiLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        supported_lines = [
            b"2024-12-12T01:44:43.728Z shell[71435]: [root]: ls -la\n",
            b"2024-03-12T07:48:40.079Z In(182) vmkernel: message\n",
            b"2021-01-04T16:02:17.168Z info hostd[526501] message\n",
            b"<166>2019-05-21T19:27:32.479Z esxi.example Hostd: info "
            b"hostd[111111] message\n",
            b"[2008-05-07 09:50:04.857 'SOAP' 2260 trivia] message\n",
        ]
        for supported_line in supported_lines:
            with self.subTest(supported_line=supported_line):
                file_object = io.BytesIO(supported_line)
                text_reader = text_parser.EncodedTextReader(file_object)
                text_reader.ReadLines()

                self.assertTrue(
                    plugin.CheckRequiredFormat(parser_mediator, text_reader)
                )

        file_object = io.BytesIO(
            b"2024-12-12T01:44:43.728Z example[71435]: not an ESXi log\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process method."""
        plugin = esxi.ESXiLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["esxi.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "component": "shell",
            "data_type": "vmware:esxi:log:entry",
            "message_body": "[root]: ls -la",
            "process_identifier": "71435",
            "written_time": "2024-12-12T01:44:43.728000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "component": "vmkernel",
            "message_body": "cpu21:2099003)<NMLX_ERR> attach failed",
            "severity": "In(182)",
            "written_time": "2024-03-12T07:48:40.079000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "component": "hostd",
            "message_body": "[Originator@6876 sub=Libs user=root] New ERROR",
            "process_identifier": "526501",
            "severity": "info",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "component": "hostd",
            "hostname": "esxi.example",
            "process_identifier": "111111",
            "severity": "info",
            "syslog_priority": "166",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        expected_components = ["auth", "vobd", "esxcli", "rhttpproxy", "vpxa"]
        for event_data_index, expected_component in enumerate(
            expected_components, start=4
        ):
            event_data = storage_writer.GetAttributeContainerByIndex(
                "event_data", event_data_index
            )
            self.assertEqual(event_data.component, expected_component)

        expected_event_values = {
            "component": "SOAP",
            "message_body": "Received soap response\nPOST /sdk HTTP/1.1",
            "process_identifier": "2260",
            "severity": "trivia",
            "written_time": "2008-05-07T09:50:04.857000",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
