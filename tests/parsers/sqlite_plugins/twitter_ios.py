#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ plugin."""

import unittest

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import twitter_ios

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class TwitterIOSTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on iOS 8+ database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'twitter_ios.db'])
  def testProcess(self):
    """Test the Process function on a Twitter iOS file."""
    plugin = twitter_ios.TwitterIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'twitter_ios.db'], plugin)

    # We should have 184 events in total.
    #  - 25 Contacts creation events.
    #  - 25 Contacts update events.
    #  - 67 Status creation events.
    #  - 67 Status update events.
    self.assertEqual(184, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    # Test the first contact creation event.
    event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2007-04-22 14:42:37')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.screen_name, u'BBCBreaking')
    self.assertEqual(event.name, u'BBC Breaking News')
    self.assertEqual(event.location, u'London, UK')
    self.assertEqual(event.following, 0)
    self.assertEqual(event.followers_count, 19466932)
    self.assertEqual(event.following_count, 3)
    self.assertEqual(event.url, u'http://www.bbc.co.uk/news')

    expected_description = (
        u'Breaking news alerts and updates from the BBC. For news, features, '
        u'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        u'sport news @BBCSport.')

    self.assertEqual(event.description, expected_description)

    expected_profile_url = (
        u'https://pbs.twimg.com/profile_images/'
        u'460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(event.profile_url, expected_profile_url)

    expected_message = (
        u'Screen name: BBCBreaking Profile picture URL: '
        u'https://pbs.twimg.com/profile_images/460740982498013184/'
        u'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        u'Description: Breaking news alerts and updates from the BBC. For '
        u'news, features, analysis follow @BBCWorld (international) or '
        u'@BBCNews (UK). Latest sport news @BBCSport. URL: '
        u'http://www.bbc.co.uk/news Following: No Number of followers: '
        u'19466932 Number of following: 3')

    expected_short_message = (
        u'Screen name: BBCBreaking Description: Breaking news alerts and '
        u'updates from t...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test first contact modification event.
    event = events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-12-02 15:35:44')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UPDATE)

    self.assertEqual(event.screen_name, u'BBCBreaking')
    self.assertEqual(event.name, u'BBC Breaking News')
    self.assertEqual(event.location, u'London, UK')
    self.assertEqual(event.following, 0)
    self.assertEqual(event.followers_count, 19466932)
    self.assertEqual(event.following_count, 3)
    self.assertEqual(event.url, u'http://www.bbc.co.uk/news')

    expected_description = (
        u'Breaking news alerts and updates from the BBC. For news, features, '
        u'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        u'sport news @BBCSport.')

    self.assertEqual(event.description, expected_description)

    expected_profile_url = (
        u'https://pbs.twimg.com/profile_images/'
        u'460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(event.profile_url, expected_profile_url)

    expected_message = (
        u'Screen name: BBCBreaking Profile picture URL: '
        u'https://pbs.twimg.com/profile_images/460740982498013184/'
        u'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        u'Description: Breaking news alerts and updates from the BBC. For '
        u'news, features, analysis follow @BBCWorld (international) or '
        u'@BBCNews (UK). Latest sport news @BBCSport. URL: '
        u'http://www.bbc.co.uk/news Following: No Number of followers: '
        u'19466932 Number of following: 3')

    expected_short_message = (
        u'Screen name: BBCBreaking Description: Breaking news alerts and '
        u'updates from t...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test first status creation event.
    event = events[50]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-09-11 11:46:16')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.text, u'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(event.user_id, 475222380)
    self.assertEqual(event.name, u'Heather Mahalik')
    self.assertEqual(event.retweet_count, 2)
    self.assertEqual(event.favorite_count, 3)
    self.assertEqual(event.favorited, 0)

    expected_message = (
        u'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        u'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        u'Count: 3')

    expected_short_message = (
        u'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test first status update event.
    event = events[51]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-12-02 15:39:37')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UPDATE)

    self.assertEqual(event.text, u'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(event.user_id, 475222380)
    self.assertEqual(event.name, u'Heather Mahalik')
    self.assertEqual(event.retweet_count, 2)
    self.assertEqual(event.favorite_count, 3)
    self.assertEqual(event.favorited, 0)

    expected_message = (
        u'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        u'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        u'Count: 3')

    expected_short_message = (
        u'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
