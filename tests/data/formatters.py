#!/usr/bin/env python3
"""Tests for the message formatters configuration files."""

import unittest

from plaso.output import mediator
from plaso.parsers.plist_plugins import macos_background_items
from plaso.parsers.plist_plugins import macos_login_items
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


if __name__ == "__main__":
    unittest.main()
