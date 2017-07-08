#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for uTorrent files."""

import unittest

from plaso.formatters import bencode_parser  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import bencode_parser

from tests import test_lib as shared_test_lib
from tests.parsers.bencode_plugins import test_lib


class UTorrentPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for uTorrent files."""

  @shared_test_lib.skipUnlessHasTestFile([u'bencode_utorrent'])
  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile([u'bencode_utorrent'], parser)

    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_caption = u'plaso test'
    expected_path = u'e:\\torrent\\files\\plaso test'

    # First test on when the torrent was added to the client.
    event = events[0]

    self.assertEqual(event.caption, expected_caption)
    self.assertEqual(event.path, expected_path)
    self.assertEqual(event.seedtime, 511)

    expected_description = definitions.TIME_DESCRIPTION_ADDED
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 14:52:12')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Second test on when the torrent file was completely downloaded.
    event = events[3]

    self.assertEqual(event.caption, expected_caption)
    self.assertEqual(event.path, expected_path)
    self.assertEqual(event.seedtime, 511)

    expected_description = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:35')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Third test on when the torrent was first modified.
    event = events[2]

    self.assertEqual(event.caption, expected_caption)
    self.assertEqual(event.path, expected_path)
    self.assertEqual(event.seedtime, 511)

    expected_description = definitions.TIME_DESCRIPTION_MODIFICATION
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 18:11:34')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Fourth test on when the torrent was again modified.
    event = events[1]

    self.assertEqual(event.caption, expected_caption)
    self.assertEqual(event.path, expected_path)
    self.assertEqual(event.seedtime, 511)

    expected_description = definitions.TIME_DESCRIPTION_MODIFICATION
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-03 16:27:59')
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
