#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Kodi videos plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import kodi

from tests.parsers.sqlite_plugins import test_lib


class KodiVideosTest(test_lib.SQLitePluginTestCase):
  """Tests for the Kodi videos database plugin."""

  def testProcess(self):
    """Test the Process function on a Kodi Videos database."""
    plugin = kodi.KodiMyVideosPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['MyVideos107.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    # Check the second event.
    expected_filename = (
        'plugin://plugin.video.youtube/play/?video_id=7WX0-O_ENlk')

    expected_event_values = {
        'filename': expected_filename,
        'timestamp': '2017-07-16 04:54:54.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = (
        'Video: plugin://plugin.video.youtube/play/?video_id=7WX0-O_ENlk '
        'Play Count: 1')
    expected_short_message = expected_filename

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
