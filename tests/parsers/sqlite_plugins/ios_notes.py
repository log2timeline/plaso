#!/usr/bin/env python3
"""Tests for the iOS Notes database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_notes

from tests.parsers.sqlite_plugins import test_lib


class IOSNotesTest(test_lib.SQLitePluginTestCase):
    """Tests for the iOS Notes database plugin."""

    def testProcess(self):
        """Test the Process function."""
        plugin = ios_notes.IOSNotesPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "NoteStore.sqlite"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "creation_time": "2020-03-28T00:42:31.589267+00:00",
            "modification_time": "2020-03-28T00:42:56.774423+00:00",
            "snippet": None,
            "title": "My Secret Note",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
