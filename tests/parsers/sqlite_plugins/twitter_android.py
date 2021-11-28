#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on Android plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import twitter_android

from tests.parsers.sqlite_plugins import test_lib


class TwitterAndroidTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on Android database plugin."""

  def testProcess(self):
    """Test the Process function on a Twitter Android file."""
    plugin = twitter_android.TwitterAndroidPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['twitter_android.db'], plugin)

    # We should have 850 events in total.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 850)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test a status event.
    expected_event_values = {
        'author_identifier': 2730978846,
        'content': (
            '@CarolMovie wins BEST PICTURE at #NYFCC!!! CONGRATS #TeamCarol!!! '
            'Love love! #carolfilm https://t.co/ycy9cHPLZ7'),
        'data_type': 'twitter:android:status',
        'date_time': '2015-12-02 17:47:17.000',
        'favorited': 0,
        'identifier': 4,
        'retweeted': 0,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'username': 'CarolMovieFans'}

    self.CheckEventValues(storage_writer, events[482], expected_event_values)

    # Test a search event.
    expected_event_values = {
        'data_type': 'twitter:android:search',
        'date_time': '2015-12-02 20:49:38.153',
        'name': 'rosegold',
        'search_query': 'rosegold',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[837], expected_event_values)

    # Test a profile creation event.
    expected_event_values = {
        'data_type': 'twitter:android:contact',
        'date_time': '2008-06-03 18:30:55.000',
        'description': (
            'Started in a San Francisco by bike messenger Rob Honeycutt, '
            'Timbuk2 has been making tough as hell messenger bags, backpacks '
            'and travel bags since 1989.'),
        'followers': 23582,
        'friends': 2725,
        'identifier': 62,
        'image_url': (
            'https://pbs.twimg.com/profile_images/461846147129024512/'
            'FOKZJ7hB_normal.jpeg'),
        'location': 'San Francisco, CA',
        'name': 'Timbuk2',
        'statuses': 18937,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'user_identifier': 14995801,
        'username': 'timbuk2',
        'web_url': 'http://t.co/Z0MZo7f2ne'}

    self.CheckEventValues(storage_writer, events[24], expected_event_values)

    # Test a friended event.
    expected_event_values = {
        'data_type': 'twitter:android:contact',
        'date_time': '2015-12-02 20:48:32.382',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[581], expected_event_values)

    # Test a profile update event.
    expected_event_values = {
        'data_type': 'twitter:android:contact',
        'date_time': '2015-12-02 20:49:33.349',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UPDATE}

    self.CheckEventValues(storage_writer, events[806], expected_event_values)


if __name__ == '__main__':
  unittest.main()
