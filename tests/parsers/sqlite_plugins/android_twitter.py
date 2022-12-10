#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on Android plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_twitter

from tests.parsers.sqlite_plugins import test_lib


class AndroidTwitterTest(test_lib.SQLitePluginTestCase):
  """Tests for Twitter on Android database plugin."""

  def testProcess(self):
    """Test the Process function on a Twitter Android file."""
    plugin = android_twitter.AndroidTwitterPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['twitter_android.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 506)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a status database entry.
    expected_event_values = {
        'author_identifier': 2730978846,
        'content': (
            '@CarolMovie wins BEST PICTURE at #NYFCC!!! CONGRATS #TeamCarol!!! '
            'Love love! #carolfilm https://t.co/ycy9cHPLZ7'),
        'creation_time': '2015-12-02T17:47:17.000+00:00',
        'data_type': 'android:twitter:status',
        'favorited': 0,
        'identifier': 4,
        'retweeted': 0,
        'username': 'CarolMovieFans'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Test a search database entry.
    expected_event_values = {
        'creation_time': '2015-12-02T20:49:38.153+00:00',
        'data_type': 'android:twitter:search',
        'name': 'rosegold',
        'search_query': 'rosegold'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a contact database entry.
    expected_event_values = {
        'creation_time': '2008-06-03T18:30:55.000+00:00',
        'data_type': 'android:twitter:contact',
        'description': (
            'Started in a San Francisco by bike messenger Rob Honeycutt, '
            'Timbuk2 has been making tough as hell messenger bags, backpacks '
            'and travel bags since 1989.'),
        'followers': 23582,
        'friends': 2725,
        'friendship_time': '2015-12-02T20:48:32.382+00:00',
        'identifier': 62,
        'image_url': (
            'https://pbs.twimg.com/profile_images/461846147129024512/'
            'FOKZJ7hB_normal.jpeg'),
        'location': 'San Francisco, CA',
        'modification_time': '2015-12-02T20:49:33.349+00:00',
        'name': 'Timbuk2',
        'statuses': 18937,
        'user_identifier': 14995801,
        'username': 'timbuk2',
        'web_url': 'http://t.co/Z0MZo7f2ne'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 323)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
