#!/usr/bin/env python3
"""Tests for the MacOS Application firewall log file text parser plugin."""

import threading
import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import macos_appfirewall

from tests.parsers.text_plugins import test_lib


def _ParseStringCompletesWithinTimeout(plugin, string, timeout=15.0):
    """Checks that parsing a string completes within a time budget.

    Args:
      plugin (TextPlugin): text log file plugin.
      string (str): string to parse.
      timeout (float): maximum number of seconds to wait.

    Returns:
      bool: True if parsing completed within the time budget.
    """

    def _Run():
        try:
            plugin._ParseString(string)  # pylint: disable=protected-access
        except errors.ParseError:
            pass

    thread = threading.Thread(target=_Run, daemon=True)
    thread.start()
    thread.join(timeout)
    return not thread.is_alive()


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

    def testParseLongLineCompletesInLinearTime(self):
        """Tests that a long line is parsed in bounded (linear) time."""
        plugin = macos_appfirewall.MacOSAppFirewallTextPlugin()

        # Many repeated-line starts without a closing "---" previously made the
        # repeated-line SkipTo scan the remainder of the buffer at every start
        # offset, so parsing was superlinear in the length of the input. It must
        # now complete quickly.
        long_text = "Nov 29 22:18:29 ---X\n" * 1500
        self.assertTrue(_ParseStringCompletesWithinTimeout(plugin, long_text))

        # A normal line still parses to the same fields.
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


if __name__ == "__main__":
    unittest.main()
