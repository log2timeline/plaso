#!/usr/bin/env python3
"""Tests for the MacOS Application firewall log file text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import macos_appfirewall

from tests.parsers.text_plugins import test_lib


class MacOSAppFirewallTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the MacOS Application firewall log file text parser plugin."""

    # pylint: disable=protected-access

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = macos_appfirewall.MacOSAppFirewallTextPlugin()

        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] <Error>: "
            b"Logging: creating /var/log/appfirewall.log\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process function."""
        plugin = macos_appfirewall.MacOSAppFirewallTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["appfirewall.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 47)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Note that added_time contains a date time delta.
        expected_event_values = {
            "action": "Allow TCP LISTEN  (in:0 out:1)",
            "added_time": "0000-11-29T22:17:30+00:00",
            "agent": "socketfilterfw[87]",
            "data_type": "macos:appfirewall_log:entry",
            "hostname": "DarkTemplar-2.local",
            "process_name": "Spotify",
            "status": "Info",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 38)
        self.CheckEventData(event_data, expected_event_values)

        # Check repeated lines.
        expected_event_values["added_time"] = "0000-11-29T22:18:29+00:00"

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 39)
        self.CheckEventData(event_data, expected_event_values)

        # Check year change.
        expected_event_values = {
            "action": "Allow TCP LISTEN  (in:0 out:1)",
            "added_time": "0001-01-01T01:13:23+00:00",
            "agent": "socketfilterfw[87]",
            "data_type": "macos:appfirewall_log:entry",
            "hostname": "DarkTemplar-2.local",
            "process_name": "Notify",
            "status": "Info",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 46)
        self.CheckEventData(event_data, expected_event_values)

    def testParseLongLine(self):
        """Tests parsing a long line."""
        plugin = macos_appfirewall.MacOSAppFirewallTextPlugin()

        # A normal line parses to its status, process name and action.
        normal_line = (
            "Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] "
            "<Info>: Dropbox: Allow TCP LISTEN  (in:0 out:1)\n"
        )
        key, structure, _, _ = plugin._ParseString(normal_line)
        self.assertEqual(key, "log_line")
        self.assertEqual(plugin._GetValueFromStructure(structure, "status"), "Info")
        self.assertEqual(
            plugin._GetStringValueFromStructure(structure, "process_name"),
            "Dropbox",
        )
        self.assertEqual(
            plugin._GetValueFromStructure(structure, "action"),
            "Allow TCP LISTEN  (in:0 out:1)",
        )

        # A repeated-line record with a long message between the "---" markers
        # parses to the repeated-line record.
        long_line = "Nov  2 04:07:35 --- " + ("x" * 50000) + " ---\n"
        key, _, _, _ = plugin._ParseString(long_line)
        self.assertEqual(key, "repeated_log_line")


if __name__ == "__main__":
    unittest.main()
