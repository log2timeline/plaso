#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on Android plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import twitter_android

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class TwitterAndroidTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on Android database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['twitter_android.db'])
  def testProcess(self):
    """Test the Process function on a Twitter Android file."""
    plugin = twitter_android.TwitterAndroidPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['twitter_android.db'], plugin)

    # We should have 850 events in total.
    self.assertEqual(850, storage_writer.number_of_events)

    events = list(storage_writer.GetSortedEvents())

    # Test status event data
    event = events[482]

    self.CheckTimestamp(event.timestamp, '2015-12-02 17:47:17.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_content = (
        '@CarolMovie wins BEST PICTURE at #NYFCC!!! CONGRATS #TeamCarol!!! '
        'Love love! #carolfilm https://t.co/ycy9cHPLZ7')

    self.assertEqual(event.author_identifier, 2730978846)
    self.assertEqual(event.content, expected_content)
    self.assertEqual(event.favorited, 0)
    self.assertEqual(event.identifier, 4)
    self.assertEqual(event.retweeted, 0)
    self.assertEqual(event.username, 'CarolMovieFans')

    expected_message = (
        'User: CarolMovieFans Status: @CarolMovie wins BEST PICTURE at '
        '#NYFCC!!! CONGRATS #TeamCarol!!! Love love! #carolfilm '
        'https://t.co/ycy9cHPLZ7 Favorited: No Retweeted: No')

    expected_short_message = (
        'User: CarolMovieFans Status: @CarolMovie wins BEST PICTURE at '
        '#NYFCC!!! CONGR...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test search event data
    event = events[837]
    self.CheckTimestamp(event.timestamp, '2015-12-02 20:49:38.153000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.name, 'rosegold')
    self.assertEqual(event.search_query, 'rosegold')

    expected_message = 'Name: rosegold Query: rosegold'

    expected_short_message = 'Query: rosegold'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test all three timestamps for contact event data.

    # Test profile creation time and event.
    event = events[24]
    self.CheckTimestamp(event.timestamp, '2008-06-03 18:30:55.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.identifier, 62)
    self.assertEqual(event.user_identifier, 14995801)
    self.assertEqual(event.username, 'timbuk2')
    self.assertEqual(event.name, 'Timbuk2')

    expected_description = (
        'Started in a San Francisco by bike messenger Rob Honeycutt, Timbuk2 '
        'has been making tough as hell messenger bags, backpacks and travel '
        'bags since 1989.')

    self.assertEqual(event.description, expected_description)
    self.assertEqual(event.web_url, 'http://t.co/Z0MZo7f2ne')
    self.assertEqual(event.location, 'San Francisco, CA')
    self.assertEqual(event.followers, 23582)
    self.assertEqual(event.friends, 2725)
    self.assertEqual(event.statuses, 18937)

    expected_image_url = (
        'https://pbs.twimg.com/profile_images/461846147129024512/'
        'FOKZJ7hB_normal.jpeg')

    self.assertEqual(event.image_url, expected_image_url)

    expected_message = (
        'Screen name: timbuk2 Profile picture URL: https://pbs.twimg.com/'
        'profile_images/461846147129024512/FOKZJ7hB_normal.jpeg Name: Timbuk2 '
        'Location: San Francisco, CA Description: Started in a San Francisco '
        'by bike messenger Rob Honeycutt, Timbuk2 has been making tough as '
        'hell messenger bags, backpacks and travel bags since 1989. URL: '
        'http://t.co/Z0MZo7f2ne Number of followers: 23582 Number of tweets: '
        '18937')

    expected_short_message = (
        'Screen name: timbuk2 Description: Started in a San Francisco by bike '
        'messenge...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test friended time.
    event = events[581]
    self.CheckTimestamp(event.timestamp, '2015-12-02 20:48:32.382000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    # Test profile update time.
    event = events[806]
    self.CheckTimestamp(event.timestamp, '2015-12-02 20:49:33.349000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UPDATE)


if __name__ == '__main__':
  unittest.main()
