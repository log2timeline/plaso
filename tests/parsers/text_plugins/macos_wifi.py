#!/usr/bin/env python3
"""Tests for the MacOS Wi-Fi log (wifi.log) files text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.containers import events
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import macos_wifi

from tests.parsers.text_plugins import test_lib


class MacOSWiFiLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the MacOS MacOS Wi-Fi log (wifi.log) files text parser plugin."""

    def _ParseDataWithPlugin(self, data, plugin):
        """Parses data as a text log file.

        Args:
          data (bytes): data of the text log file.
          plugin (TextPlugin): text log file plugin.

        Returns:
          FakeStorageWriter: storage writer.
        """
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile("/wifi.log", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/wifi.log")

        storage_writer = self._CreateStorageWriter()

        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        event_data_stream = events.EventDataStream()
        event_data_stream.path_spec = file_entry.path_spec
        parser_mediator.ProduceEventDataStream(event_data_stream)

        parser_mediator.AppendToParserChain("text")

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(
            file_object, encoding=plugin.ENCODING
        )
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

        return storage_writer

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = macos_wifi.MacOSWiFiLogTextPlugin()

        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"Thu Nov 14 20:14:37.123 ***Starting Up***\n"
                b"Thu Nov 14 20:36:37.222 <airportd[88]> airportdProcessDLILEvent: "
                b"en0 attached (up)\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
                b"content in image.dd.\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check a log line without a date and time value on the first line.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"<airportd[123]> _processIPv4Changes: ARP/NDP offloads disabled, "
                b"not programming the offload\n"
                b"Mon Sep 30 17:13:41.891 <airportd[123]> ERROR: rapportd (283) is "
                b"not entitled for com.apple.wifi.events\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process function."""
        plugin = macos_wifi.MacOSWiFiLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["wifi.log"], plugin)

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
            "action": "Interface en0 turn up.",
            "added_time": "0000-11-14T20:36:37.222+00:00",
            "agent": "airportd[88]",
            "data_type": "macos:wifi_log:entry",
            "function": "airportdProcessDLILEvent",
            "text": "en0 attached (up)",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Check year change.
        expected_event_values = {
            "action": "Wi-Fi connected to SSID: AndroidAP",
            "added_time": "0001-01-01T01:12:17.311+00:00",
            "agent": "airportd[88]",
            "data_type": "macos:wifi_log:entry",
            "function": "_doAutoJoin",
            "text": "Already associated to “AndroidAP”. Bailing on auto-join.",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithTurnedOverLog(self):
        """Tests the Process function with a turned over log file."""
        plugin = macos_wifi.MacOSWiFiLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["wifi_turned_over.log"], plugin)

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

        expected_event_values = {
            "action": None,
            "added_time": "0000-01-02T00:10:15+00:00",
            "agent": None,
            "data_type": "macos:wifi_log:entry",
            "function": None,
            "text": "test-macbookpro newsyslog[50498]: logfile turned over",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "action": None,
            "added_time": "0000-01-02T00:11:02.378+00:00",
            "agent": None,
            "data_type": "macos:wifi_log:entry",
            "function": None,
            "text": (
                "<kernel> wl0: powerChange: *** "
                "BONJOUR/MDNS OFFLOADS ARE NOT RUNNING."
            ),
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithContinuationLine(self):
        """Tests the Process function with a line without date and time value."""
        plugin = macos_wifi.MacOSWiFiLogTextPlugin()
        storage_writer = self._ParseDataWithPlugin(
            (
                b"Mon Sep 30 17:13:22.751 <airportd[123]> ERROR: SecurityAgent (228) "
                b"is not entitled for com.apple.wifi.events, but allowing anyways "
                b"for event type 6\n"
                b"<airportd[123]> _processIPv4Changes: ARP/NDP offloads disabled, "
                b"not programming the offload\n"
                b"Mon Sep 30 17:13:41.891 <airportd[123]> airportdProcessDLILEvent: "
                b"en0 attached (up)\n"
            ),
            plugin,
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "action": None,
            "added_time": "0000-09-30T17:13:22.751+00:00",
            "agent": None,
            "data_type": "macos:wifi_log:entry",
            "function": None,
            "text": (
                "<airportd[123]> ERROR: SecurityAgent (228) is not entitled for "
                "com.apple.wifi.events, but allowing anyways for event type 6 "
                "<airportd[123]> _processIPv4Changes: ARP/NDP offloads disabled, "
                "not programming the offload"
            ),
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # The log line after the continuation line is not changed.
        expected_event_values = {
            "action": "Interface en0 turn up.",
            "added_time": "0000-09-30T17:13:41.891+00:00",
            "agent": "airportd[123]",
            "data_type": "macos:wifi_log:entry",
            "function": "airportdProcessDLILEvent",
            "text": "en0 attached (up)",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
