#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for uTorrent files."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import bencode_parser as bencode_formatter
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class UTorrentPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for uTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser_object = bencode_parser.BencodeParser()

    storage_writer = self._ParseFile(
        [u'bencode_utorrent'], parser_object)

    self.assertEqual(len(storage_writer.events), 4)

    expected_caption = u'plaso test'
    expected_path = u'e:\\torrent\\files\\plaso test'

    # First test on when the torrent was added to the client.
    event_object = storage_writer.events[3]

    self.assertEqual(event_object.caption, expected_caption)
    self.assertEqual(event_object.path, expected_path)
    self.assertEqual(event_object.seedtime, 511)

    expected_description = eventdata.EventTimestamp.ADDED_TIME
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 14:52:12')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Second test on when the torrent file was completely downloaded.
    event_object = storage_writer.events[2]

    self.assertEqual(event_object.caption, expected_caption)
    self.assertEqual(event_object.path, expected_path)
    self.assertEqual(event_object.seedtime, 511)

    expected_description = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:35')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Third test on when the torrent was first modified.
    event_object = storage_writer.events[0]

    self.assertEqual(event_object.caption, expected_caption)
    self.assertEqual(event_object.path, expected_path)
    self.assertEqual(event_object.seedtime, 511)

    expected_description = eventdata.EventTimestamp.MODIFICATION_TIME
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:34')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Fourth test on when the torrent was again modified.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.caption, expected_caption)
    self.assertEqual(event_object.path, expected_path)
    self.assertEqual(event_object.seedtime, 511)

    expected_description = eventdata.EventTimestamp.MODIFICATION_TIME
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 16:27:59')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
