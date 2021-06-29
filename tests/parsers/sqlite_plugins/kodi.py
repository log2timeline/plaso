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

    self.assertEqual(storage_writer.number_of_events, 4)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'kodi:videos:viewing',
        'date_time': '2017-07-16 04:54:54',
        'filename': 'plugin://plugin.video.youtube/play/?video_id=7WX0-O_ENlk',
        'play_count': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
