#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ plugin."""

import unittest

from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import twitter_ios
from tests.parsers.sqlite_plugins import test_lib


class TwitterIOSTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on iOS 8+ database plugin."""

  def testProcess(self):
    """Test the Process function on a Twitter iOS file."""
    plugin_object = twitter_ios.TwitterIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'twitter_ios.db'], plugin_object)

    # We should have 184 events in total.
    #  - 25 Contacts creation events.
    #  - 25 Contacts update events.
    #  - 67 Status creation events.
    #  - 67 Status update events.
    self.assertEqual(184, len(storage_writer.events))

    # Test the first contact creation event.
    test_event = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2007-04-22 14:42:37')
    self.assertEqual(test_event.timestamp, expected_timestamp)

    self.assertEqual(
        test_event.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    self.assertEqual(test_event.screen_name, u'BBCBreaking')
    self.assertEqual(test_event.name, u'BBC Breaking News')
    self.assertEqual(test_event.location, u'London, UK')
    self.assertEqual(test_event.following, 0)
    self.assertEqual(test_event.followers_cnt, 19466932)
    self.assertEqual(test_event.following_cnt, 3)
    self.assertEqual(test_event.url, u'http://www.bbc.co.uk/news')

    expected_description = (
        u'Breaking news alerts and updates from the BBC. For news, features, '
        u'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        u'sport news @BBCSport.')

    self.assertEqual(test_event.description, expected_description)

    expected_profile_url = (
        u'https://pbs.twimg.com/profile_images/'
        u'460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(test_event.profile_url, expected_profile_url)

    expected_msg = (
        u'Screen name: BBCBreaking Profile picture URL: '
        u'https://pbs.twimg.com/profile_images/460740982498013184/'
        u'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        u'Description: Breaking news alerts and updates from the BBC. For '
        u'news, features, analysis follow @BBCWorld (international) or '
        u'@BBCNews (UK). Latest sport news @BBCSport. URL: '
        u'http://www.bbc.co.uk/news Following: No Number of followers: '
        u'19466932 Number of following: 3')

    expected_msg_short = (
        u'Screen name: BBCBreaking Description: Breaking news alerts and '
        u'updates from t...')

    self._TestGetMessageStrings(test_event, expected_msg, expected_msg_short)

    # Test first contact modification event.
    test_event = storage_writer.events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-12-02 15:35:44')
    self.assertEqual(test_event.timestamp, expected_timestamp)

    self.assertEqual(
        test_event.timestamp_desc, eventdata.EventTimestamp.UPDATE_TIME)

    self.assertEqual(test_event.screen_name, u'BBCBreaking')
    self.assertEqual(test_event.name, u'BBC Breaking News')
    self.assertEqual(test_event.location, u'London, UK')
    self.assertEqual(test_event.following, 0)
    self.assertEqual(test_event.followers_cnt, 19466932)
    self.assertEqual(test_event.following_cnt, 3)
    self.assertEqual(test_event.url, u'http://www.bbc.co.uk/news')

    expected_description = (
        u'Breaking news alerts and updates from the BBC. For news, features, '
        u'analysis follow @BBCWorld (international) or @BBCNews (UK). Latest '
        u'sport news @BBCSport.')

    self.assertEqual(test_event.description, expected_description)

    expected_profile_url = (
        u'https://pbs.twimg.com/profile_images/'
        u'460740982498013184/wIPwMwru_normal.png')

    self.assertEqual(test_event.profile_url, expected_profile_url)

    expected_msg = (
        u'Screen name: BBCBreaking Profile picture URL: '
        u'https://pbs.twimg.com/profile_images/460740982498013184/'
        u'wIPwMwru_normal.png Name: BBC Breaking News Location: London, UK '
        u'Description: Breaking news alerts and updates from the BBC. For '
        u'news, features, analysis follow @BBCWorld (international) or '
        u'@BBCNews (UK). Latest sport news @BBCSport. URL: '
        u'http://www.bbc.co.uk/news Following: No Number of followers: '
        u'19466932 Number of following: 3')

    expected_msg_short = (
        u'Screen name: BBCBreaking Description: Breaking news alerts and '
        u'updates from t...')

    self._TestGetMessageStrings(test_event, expected_msg, expected_msg_short)

    # Test first status creation event.
    test_event = storage_writer.events[50]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-09-11 11:46:16')
    self.assertEqual(test_event.timestamp, expected_timestamp)

    self.assertEqual(
        test_event.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    self.assertEqual(test_event.text, u'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(test_event.user_id, 475222380)
    self.assertEqual(test_event.name, u'Heather Mahalik')
    self.assertEqual(test_event.retweet_cnt, 2)
    self.assertEqual(test_event.favorite_cnt, 3)
    self.assertEqual(test_event.favorited, 0)

    expected_msg = (
        u'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        u'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        u'Count: 3')

    expected_msg_short = (
        u'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(test_event, expected_msg, expected_msg_short)

    # Test first status update event.
    test_event = storage_writer.events[51]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-12-02 15:39:37')
    self.assertEqual(test_event.timestamp, expected_timestamp)

    self.assertEqual(
        test_event.timestamp_desc, eventdata.EventTimestamp.UPDATE_TIME)

    self.assertEqual(test_event.text, u'Never forget. http://t.co/L7bjWue1A2')
    self.assertEqual(test_event.user_id, 475222380)
    self.assertEqual(test_event.name, u'Heather Mahalik')
    self.assertEqual(test_event.retweet_cnt, 2)
    self.assertEqual(test_event.favorite_cnt, 3)
    self.assertEqual(test_event.favorited, 0)

    expected_msg = (
        u'Name: Heather Mahalik User Id: 475222380 Message: Never forget. '
        u'http://t.co/L7bjWue1A2 Favorite: No Retweet Count: 2 Favorite '
        u'Count: 3')

    expected_msg_short = (
        u'Name: Heather Mahalik Message: Never forget. http://t.co/L7bjWue1A2')

    self._TestGetMessageStrings(test_event, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
