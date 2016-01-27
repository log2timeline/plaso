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

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = bencode_parser.BencodeParser()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath([u'bencode_utorrent'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 4)

    caption_expected = u'plaso test'
    path_expected = u'e:\\torrent\\files\\plaso test'

    # First test on when the torrent was added to the client.
    event_object = event_objects[0]

    self.assertEqual(event_object.caption, caption_expected)

    self.assertEqual(event_object.path, path_expected)

    self.assertEqual(event_object.seedtime, 511)

    description_expected = eventdata.EventTimestamp.ADDED_TIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 14:52:12')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Second test on when the torrent file was completely downloaded.
    event_object = event_objects[3]

    self.assertEqual(event_object.caption, caption_expected)
    self.assertEqual(event_object.path, path_expected)
    self.assertEqual(event_object.seedtime, 511)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:35')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Third test on when the torrent was first modified.
    event_object = event_objects[2]

    self.assertEqual(event_object.caption, caption_expected)
    self.assertEqual(event_object.path, path_expected)
    self.assertEqual(event_object.seedtime, 511)

    description_expected = eventdata.EventTimestamp.MODIFICATION_TIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:34')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Fourth test on when the torrent was again modified.
    event_object = event_objects[1]

    self.assertEqual(event_object.caption, caption_expected)
    self.assertEqual(event_object.path, path_expected)
    self.assertEqual(event_object.seedtime, 511)

    description_expected = eventdata.EventTimestamp.MODIFICATION_TIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 16:27:59')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
