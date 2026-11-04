#!/usr/bin/env python3
"""Tests for the bencode parser plugin for uTorrent files."""

import unittest

import bencode

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class UTorrentPluginTest(test_lib.BencodePluginTestCase):
    """Tests for bencode parser plugin for uTorrent files."""

    def _ParseBencodeData(self, decoded_values):
        """Parses bencoded data with the uTorrent plugin.

        Args:
          decoded_values (dict[str, object]): values to bencode.

        Returns:
          FakeStorageWriter: storage writer.
        """
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile("/resume.dat", bencode.bencode(decoded_values))

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/resume.dat")

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        parser = bencode_parser.BencodeParser()
        parser.EnablePlugins(["bencode_utorrent"])

        file_object = file_entry.GetFileObject()
        parser.ParseFileObject(parser_mediator, file_object)

        return storage_writer

    def testProcess(self):
        """Tests the Process function."""
        parser = bencode_parser.BencodeParser()
        storage_writer = self._ParseFile(["bencode", "utorrent"], parser)

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
            "added_time": "2013-08-03T14:52:12+00:00",
            "caption": "plaso test",
            "data_type": "p2p:bittorrent:utorrent",
            "destination": "e:\\torrent\\files\\plaso test",
            "downloaded_time": "2013-08-03T18:11:35+00:00",
            "modification_times": [
                "2013-08-03T18:11:34+00:00",
                "2013-08-03T16:27:59+00:00",
            ],
            "seedtime": 511,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithMultipleTorrents(self):
        """Tests the Process function with multiple torrents."""
        storage_writer = self._ParseBencodeData(
            {
                ".fileguard": "38A3065312D01D8226326BCCCD1F829700B43A55",
                "e:\\torrent\\cache\\first.torrent": {
                    "added_on": 1375541532,
                    "caption": "first",
                    "seedtime": 30660,
                },
                "e:\\torrent\\cache\\second.torrent": {
                    "added_on": 1375541533,
                    "caption": "second",
                    "seedtime": 120,
                },
            }
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2013-08-03T14:52:12+00:00",
            "caption": "first",
            "data_type": "p2p:bittorrent:utorrent",
            "seedtime": 511,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "added_time": "2013-08-03T14:52:13+00:00",
            "caption": "second",
            "data_type": "p2p:bittorrent:utorrent",
            "seedtime": 2,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithoutSeedtime(self):
        """Tests the Process function with a torrent without seed time."""
        storage_writer = self._ParseBencodeData(
            {
                ".fileguard": "38A3065312D01D8226326BCCCD1F829700B43A55",
                "e:\\torrent\\cache\\first.torrent": {
                    "added_on": 1375541532,
                    "caption": "first",
                },
                "e:\\torrent\\cache\\second.torrent": {
                    "added_on": 1375541533,
                    "caption": "second",
                    "seedtime": 120,
                },
            }
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "caption": "first",
            "data_type": "p2p:bittorrent:utorrent",
            "seedtime": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithoutTorrents(self):
        """Tests the Process function without torrents."""
        storage_writer = self._ParseBencodeData(
            {".fileguard": "38A3065312D01D8226326BCCCD1F829700B43A55"}
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
