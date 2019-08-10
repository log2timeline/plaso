#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import twitter_ios

from tests.parsers.sqlite_plugins import test_lib


class TwitterIOSTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on iOS 8+ database plugin."""

  def testProcess(self):
    """Test the Process function on a Twitter iOS file."""
    plugin = twitter_ios.TwitterIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['twitter_ios.db'], plugin)

    # We should have 184 events in total.
    #  - 25 Contacts creation events.
    #  - 25 Contacts update events.
    #  - 67 Status creation events.
    #  - 67 Status update events.
    self.assertEqual(184, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    # Test the first contact creation event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2007-04-22 14:42:37.000000')

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.screen_name, 'BBCBreaking')
    self.assertEqual(event_data.name, 'BBC Breaking News')
    self.assertEqual(event_data.location, 'London, UK')
    self.assertEqual(event_data.following, 0)
    self.assertEqual(event_data.followers_count, 19466932)
    self.assertEqual(event_data.following_count, 3)
    self.assertEqual(event_data.url, 'http://www.bbc.co.uk/news')

    expected_description = (
        'Breaking news alerts and updates from the BBC. For news, features, '
        'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        'sport news @BBCSport.')

    self.assertEqual(event_data.description, expected_description)

    expected_profile_url = (
        'https://pbs.twimg.com/profile_images/'
        '460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(event_data.profile_url, expected_profile_url)

    expected_message = (
        'Screen name: BBCBreaking Profile picture URL: '
        'https://pbs.twimg.com/profile_images/460740982498013184/'
        'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        'Description: Breaking news alerts and updates from the BBC. For '
        'news, features, analysis follow @BBCWorld (international) or '
        '@BBCNews (UK). Latest sport news @BBCSport. URL: '
        'http://www.bbc.co.uk/news Following: No Number of followers: '
        '19466932 Number of following: 3')

    expected_short_message = (
        'Screen name: BBCBreaking Description: Breaking news alerts and '
        'updates from t...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test first contact modification event.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-12-02 15:35:44.000000')

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UPDATE)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.screen_name, 'BBCBreaking')
    self.assertEqual(event_data.name, 'BBC Breaking News')
    self.assertEqual(event_data.location, 'London, UK')
    self.assertEqual(event_data.following, 0)
    self.assertEqual(event_data.followers_count, 19466932)
    self.assertEqual(event_data.following_count, 3)
    self.assertEqual(event_data.url, 'http://www.bbc.co.uk/news')

    expected_description = (
        'Breaking news alerts and updates from the BBC. For news, features, '
        'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        'sport news @BBCSport.')

    self.assertEqual(event_data.description, expected_description)

    expected_profile_url = (
        'https://pbs.twimg.com/profile_images/'
        '460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(event_data.profile_url, expected_profile_url)

    expected_message = (
        'Screen name: BBCBreaking Profile picture URL: '
        'https://pbs.twimg.com/profile_images/460740982498013184/'
        'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        'Description: Breaking news alerts and updates from the BBC. For '
        'news, features, analysis follow @BBCWorld (international) or '
        '@BBCNews (UK). Latest sport news @BBCSport. URL: '
        'http://www.bbc.co.uk/news Following: No Number of followers: '
        '19466932 Number of following: 3')

    expected_short_message = (
        'Screen name: BBCBreaking Description: Breaking news alerts and '
        'updates from t...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test first status creation event.
    event = events[50]

    self.CheckTimestamp(event.timestamp, '2014-09-11 11:46:16.000000')

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.text, 'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(event_data.user_id, 475222380)
    self.assertEqual(event_data.name, 'Heather Mahalik')
    self.assertEqual(event_data.retweet_count, 2)
    self.assertEqual(event_data.favorite_count, 3)
    self.assertEqual(event_data.favorited, 0)

    expected_message = (
        'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        'Count: 3')

    expected_short_message = (
        'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test first status update event.
    event = events[51]

    self.CheckTimestamp(event.timestamp, '2015-12-02 15:39:37.000000')

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UPDATE)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.text, 'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(event_data.user_id, 475222380)
    self.assertEqual(event_data.name, 'Heather Mahalik')
    self.assertEqual(event_data.retweet_count, 2)
    self.assertEqual(event_data.favorite_count, 3)
    self.assertEqual(event_data.favorited, 0)

    expected_message = (
        'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        'Count: 3')

    expected_short_message = (
        'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
