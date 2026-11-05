#!/usr/bin/env python3
"""Tests for the FreeDesktop.org Trash info text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import trash_info

from tests.parsers.text_plugins import test_lib


class TrashInfoTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the FreeDesktop.org Trash info text parser plugin."""

    def _CheckRequiredFormat(self, plugin, data):
        """Checks the required format of data.

        Args:
          plugin (TrashInfoTextPlugin): plugin.
          data (bytes): data.

        Returns:
          bool: True if the data has the format required by the plugin.
        """
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(data)
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        return plugin.CheckRequiredFormat(parser_mediator, text_reader)

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = trash_info.TrashInfoTextPlugin()

        result = self._CheckRequiredFormat(
            plugin,
            b"[Trash Info]\n"
            b"Path=/home/user/notes.txt\n"
            b"DeletionDate=2022-08-19T14:05:31\n",
        )
        self.assertTrue(result)

        # Check a Trash info file with the deletion date before the path.
        result = self._CheckRequiredFormat(
            plugin,
            b"[Trash Info]\n"
            b"DeletionDate=2022-08-19T14:05:31\n"
            b"Path=/home/user/notes.txt\n",
        )
        self.assertTrue(result)

        # Check a desktop entry file, which has a similar format.
        result = self._CheckRequiredFormat(
            plugin, b"[Desktop Entry]\nType=Application\nPath=/home/user\n"
        )
        self.assertFalse(result)

        # Check a file where the Trash info group is not on the first line.
        result = self._CheckRequiredFormat(
            plugin,
            b"# Comment\n"
            b"[Trash Info]\n"
            b"Path=/home/user/notes.txt\n"
            b"DeletionDate=2022-08-19T14:05:31\n",
        )
        self.assertFalse(result)

        # Check a file with a Trash info group without Path or DeletionDate.
        result = self._CheckRequiredFormat(plugin, b"[Trash Info]\nName=notes.txt\n")
        self.assertFalse(result)

        # Check a file with a deletion date in an unsupported format.
        result = self._CheckRequiredFormat(
            plugin, b"[Trash Info]\nDeletionDate=19/08/2022 14:05:31\n"
        )
        self.assertFalse(result)

        # Check non-matching format.
        result = self._CheckRequiredFormat(
            plugin,
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n",
        )
        self.assertFalse(result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = trash_info.TrashInfoTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["meeting_notes.txt.trashinfo"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "linux:trash_info:entry",
            "deletion_time": "2022-08-19T14:05:31",
            "original_path": "/home/user/Documents/meeting notes été.txt",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithInvalidDeletionDate(self):
        """Tests the Process function with an invalid deletion date."""
        plugin = trash_info.TrashInfoTextPlugin()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject(
            "notes.txt.trashinfo",
            b"[Trash Info]\n"
            b"Path=/home/user/notes.txt\n"
            b"DeletionDate=2022-13-45T14:05:31\n",
        )
        plugin.Process(parser_mediator, file_object=file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "data_type": "linux:trash_info:entry",
            "deletion_time": None,
            "original_path": "/home/user/notes.txt",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
