#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ plugin."""

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
    # * 25 Contacts creation events.
    # * 25 Contacts update events.
    # * 67 Status creation events.
    # * 67 Status update events.

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 184)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Test the first contact creation event.
    expected_event_values = {
        'data_type': 'twitter:ios:contact',
        'date_time': '2007-04-22 14:42:37',
        'description': (
            'Breaking news alerts and updates from the BBC. For news, '
            'features, analysis follow @BBCWorld (international) or @BBCNews '
            '(UK). Latest sport news @BBCSport.'),
        'followers_count': 19466932,
        'following': 0,
        'following_count': 3,
        'location': 'London, UK',
        'name': 'BBC Breaking News',
        'profile_url': (
            'https://pbs.twimg.com/profile_images/460740982498013184/'
            'wIPwMwru_normal.png'),
        'screen_name': 'BBCBreaking',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'url': 'http://www.bbc.co.uk/news'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test a contact modification event.
    expected_event_values = {
        'data_type': 'twitter:ios:contact',
        'date_time': '2015-12-02 15:35:44',
        'description': (
            'Breaking news alerts and updates from the BBC. For news, '
            'features, analysis follow @BBCWorld (international) or @BBCNews '
            '(UK). Latest sport news @BBCSport.'),
        'followers_count': 19466932,
        'following': 0,
        'following_count': 3,
        'location': 'London, UK',
        'name': 'BBC Breaking News',
        'profile_url': (
            'https://pbs.twimg.com/profile_images/'
            '460740982498013184/wIPwMwru_normal.png'),
        'screen_name': 'BBCBreaking',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UPDATE,
        'url': 'http://www.bbc.co.uk/news'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test a status creation event.
    expected_event_values = {
        'data_type': 'twitter:ios:status',
        'date_time': '2014-09-11 11:46:16',
        'favorite_count': 3,
        'favorited': 0,
        'name': 'Heather Mahalik',
        'retweet_count': 2,
        'text': 'Never forget. http://t.co/L7bjWue1A2',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'user_id': 475222380}

    self.CheckEventValues(storage_writer, events[50], expected_event_values)

    # Test a status update event.
    expected_event_values = {
        'data_type': 'twitter:ios:status',
        'date_time': '2015-12-02 15:39:37',
        'favorite_count': 3,
        'favorited': 0,
        'name': 'Heather Mahalik',
        'retweet_count': 2,
        'text': 'Never forget. http://t.co/L7bjWue1A2',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UPDATE,
        'user_id': 475222380}

    self.CheckEventValues(storage_writer, events[51], expected_event_values)


if __name__ == '__main__':
  unittest.main()
