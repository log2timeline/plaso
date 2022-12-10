#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_twitter

from tests.parsers.sqlite_plugins import test_lib


class IOSTwitterTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on iOS 8+ SQLite database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_twitter.IOSTwitterPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['twitter_ios.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 92)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a contact database entry.
    expected_event_values = {
        'creation_time': '2007-04-22T14:42:37+00:00',
        'data_type': 'ios:twitter:contact',
        'description': (
            'Breaking news alerts and updates from the BBC. For news, '
            'features, analysis follow @BBCWorld (international) or @BBCNews '
            '(UK). Latest sport news @BBCSport.'),
        'followers_count': 19466932,
        'following': 0,
        'following_count': 3,
        'location': 'London, UK',
        'modification_time': '2015-12-02T15:35:44+00:00',
        'name': 'BBC Breaking News',
        'profile_url': (
            'https://pbs.twimg.com/profile_images/460740982498013184/'
            'wIPwMwru_normal.png'),
        'screen_name': 'BBCBreaking',
        'url': 'http://www.bbc.co.uk/news'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a status database entry.
    expected_event_values = {
        'creation_time': '2014-09-11T11:46:16+00:00',
        'data_type': 'ios:twitter:status',
        'favorite_count': 3,
        'favorited': 0,
        'modification_time': '2015-12-02T15:39:37+00:00',
        'name': 'Heather Mahalik',
        'retweet_count': 2,
        'text': 'Never forget. http://t.co/L7bjWue1A2',
        'user_identifier': 475222380}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 25)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
