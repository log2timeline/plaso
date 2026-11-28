#!/usr/bin/env python3
"""Tests for the message formatters configuration files."""

import glob
import os
import re
import unittest

import yaml

from acstore.containers import interface as containers_interface

from dfdatetime import filetime as dfdatetime_filetime

from plaso.output import mediator
from plaso.parsers.plist_plugins import launchd
from plaso.parsers.plist_plugins import macos_background_items
from plaso.parsers.plist_plugins import macos_login_items
from plaso.parsers.plist_plugins import spotlight_searched_terms
from plaso.parsers.winreg_plugins import bagmru
from plaso.parsers.winreg_plugins import diagnosed_applications
from plaso.storage.fake import writer as fake_writer

from tests.parsers.plist_plugins import test_lib as plist_plugins_test_lib


class MessageFormattersDataTest(plist_plugins_test_lib.PlistPluginTestCase):
    """Tests the message formatters configuration files."""

    def _GetMessages(self, formatters_file_name, event_data):
        """Retrieves the message and short message of event data.

        Args:
          formatters_file_name (str): name of the message formatters file.
          event_data (EventData): event data.

        Returns:
          tuple[str, str]: message and short message.
        """
        event_data_stream_identifier = (
            containers_interface.AttributeContainerIdentifier(
                name="event_data_stream", sequence_number=1
            )
        )
        event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)
            output_mediator.ReadMessageFormattersFromFile(
                self._GetDataFilePath(["formatters", formatters_file_name])
            )

            message_formatter = output_mediator.GetMessageFormatter(
                event_data.data_type
            )
            self.assertIsNotNone(message_formatter)

            event_values = event_data.CopyToDict()
            message_formatter.FormatEventValues(output_mediator, event_values)

            message = message_formatter.GetMessage(event_values)
            message_short = message_formatter.GetMessageShort(event_values)

        finally:
            storage_writer.Close()

        return message, message_short

    def testBagMRUMessage(self):
        """Tests the windows:registry:bagmru message."""
        event_data = bagmru.BagMRUEventData()
        event_data.entries = "Index: 1 [MRU Value 0]: Shell item path: <My Computer>"
        event_data.key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU"
        )
        event_data.last_written_time = dfdatetime_filetime.Filetime(
            timestamp=0x01CB3A623D0A17CE
        )

        expected_message = (
            "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU] "
            "Index: 1 [MRU Value 0]: Shell item path: <My Computer>"
        )
        message, message_short = self._GetMessages("windows.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, f"{expected_message[:77]:s}...")

        # A BagMRU key without entries.
        event_data.entries = None

        expected_message = (
            "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU]"
        )
        message, message_short = self._GetMessages("windows.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, expected_message)

    def testDiagnosedApplicationsMessage(self):
        """Tests the windows:registry:diagnosed_applications message."""
        event_data = diagnosed_applications.DiagnosedApplicationsEventData()
        event_data.key_path = (
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\RADAR\\HeapLeakDetection\\"
            "DiagnosedApplications\\TrustedInstaller.exe"
        )
        event_data.last_detection_time = dfdatetime_filetime.Filetime(
            timestamp=0x01CB3A623D0A17CE
        )
        event_data.last_written_time = dfdatetime_filetime.Filetime(
            timestamp=0x01CB3A623D0A17CE
        )
        event_data.process_name = "TrustedInstaller.exe"

        expected_message = (
            "Process Name: TrustedInstaller.exe "
            "Origin: HKEY_LOCAL_MACHINE\\Software\\Microsoft\\RADAR\\"
            "HeapLeakDetection\\DiagnosedApplications\\TrustedInstaller.exe"
        )
        message, message_short = self._GetMessages("windows.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, "Process Name: TrustedInstaller.exe")

    def testFormatStrings(self):
        """Tests that labels in the format strings are followed by ": "."""
        # A label is a word directly followed by a colon. A colon that is not
        # preceded by a word character, such as in "{host}:{port}" or
        # ":{port}", or that is followed by a path separator, such as in
        # "http://", is not considered a label separator.
        attribute_name_regex = re.compile(r"{[^}]*}")
        label_separator_regex = re.compile(r"[A-Za-z0-9_]:(?![ /\\]|$)")

        formatters_path = self._GetDataFilePath(["formatters"])
        for path in sorted(glob.glob(os.path.join(formatters_path, "*.yaml"))):
            with open(path, encoding="utf-8") as file_object:
                formatter_definitions = list(yaml.safe_load_all(file_object))

            for formatter_definition in formatter_definitions:
                for key in ("message", "short_message"):
                    format_string_pieces = formatter_definition.get(key) or []
                    if isinstance(format_string_pieces, str):
                        format_string_pieces = [format_string_pieces]

                    for format_string_piece in format_string_pieces:
                        format_string_piece = attribute_name_regex.sub(
                            "{}", format_string_piece
                        )
                        self.assertIsNone(
                            label_separator_regex.search(format_string_piece),
                            msg=(
                                f"{os.path.basename(path):s} "
                                f"{formatter_definition['data_type']:s} {key:s}: "
                                f"{format_string_piece:s}"
                            ),
                        )

    def testMacOSBackgroundItemsMessage(self):
        """Tests the macos:background_items:entry message."""
        plist_name = "backgrounditems.btm"

        plugin = macos_background_items.MacOSBackgroundItemsPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, [plist_name], plist_name
        )
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)

        expected_message = (
            "Login item: iTunesHelper "
            "Points to: /Applications/iTunes.app/Contents/MacOS/iTunesHelper.app "
            "Volume name: Macintosh HD "
            "Volume mount point: / "
            "Volume flags: IsLocal, IsInternal, SupportsPersistentIDs"
        )
        expected_short_message = (
            "Login item iTunesHelper "
            "points to /Applications/iTunes.app/Contents/MacOS/iTunesHelper.app"
        )
        message, message_short = self._GetMessages("macos.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, f"{expected_short_message[:77]:s}...")

    def testMacOSLaunchdMessage(self):
        """Tests the macos:launchd:entry message."""
        event_data = launchd.MacOSLaunchdEventData()
        event_data.group_name = "wheel"
        event_data.name = "com.foobar.test"
        event_data.program = "/Test --flag 1"
        event_data.username = "root"

        expected_message = (
            "Launchd service config com.foobar.test points to /Test --flag 1 "
            "with user: root group: wheel"
        )
        message, message_short = self._GetMessages("macos.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, f"{expected_message[:77]:s}...")

        # A launchd plist without user and group name.
        event_data.group_name = None
        event_data.username = None

        expected_message = (
            "Launchd service config com.foobar.test points to /Test --flag 1"
        )
        message, message_short = self._GetMessages("macos.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, expected_message)

    def testMacOSLoginItemsMessage(self):
        """Tests the macos:login_items:entry message."""
        plist_name = "com.apple.loginitems.plist"

        plugin = macos_login_items.MacOSLoginItemsPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, ["plist", plist_name], plist_name
        )
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)

        expected_message = (
            "Login item: iTunesHelper "
            "Points to: /Applications/iTunes.app/Contents/MacOS/iTunesHelper.app "
            "Volume name: Macintosh HD "
            "Volume mount point: / "
            "Volume flags: IsBootVolume, HasPersistentFileIds"
        )
        expected_short_message = (
            "Login item iTunesHelper "
            "points to /Applications/iTunes.app/Contents/MacOS/iTunesHelper.app"
        )
        message, message_short = self._GetMessages("macos.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, f"{expected_short_message[:77]:s}...")

    def testSpotlightSearchedTermsMessage(self):
        """Tests the spotlight_searched_terms:entry message."""
        event_data = spotlight_searched_terms.SpotlightSearchedTermsEventData()
        event_data.application_display_name = "Grab"
        event_data.path = "/Applications/Utilities/Grab.app"
        event_data.search_term = "gr"

        expected_message = (
            'Spotlight term searched "gr" associate to Grab '
            "(/Applications/Utilities/Grab.app)"
        )
        message, message_short = self._GetMessages("macos.yaml", event_data)
        self.assertEqual(message, expected_message)
        self.assertEqual(message_short, f"{expected_message[:77]:s}...")


if __name__ == "__main__":
    unittest.main()
