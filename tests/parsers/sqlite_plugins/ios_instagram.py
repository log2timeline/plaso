#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Kik messenger SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_instagram

from tests.parsers.sqlite_plugins import test_lib


class IOSInstagramThreadsTest(test_lib.SQLitePluginTestCase):
  """Tests for the iOS Kik messenger SQLite database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_instagram.IOSInstagramPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['9368974384.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 75)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'sent_time': '2020-03-22T19:12:02.808456+00:00',
        'sender_pk': '9368974384',
        'message': None,
        'video_chat_title': 'Video chat ended',
        'video_chat_call_id': '18135614113062170',
        'shared_media_id': None,
        'shared_media_url': None,
        'username': 'ThisIsDFIR' }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'sent_time': '2020-03-25T01:41:17.164115+00:00',
        'sender_pk': '22824420',
        'message': 'Clicked over to Threads. '
        'I still do not understand why this app exists.',
        'video_chat_title': None,
        'video_chat_call_id': None,
        'shared_media_id': None,
        'shared_media_url': None,
        'username': None }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'sent_time': '2020-03-25T01:49:04.901623+00:00',
        'sender_pk': '9368974384',
        'message': None,
        'video_chat_title': None,
        'video_chat_call_id': None,
        'shared_media_id': '251704772664178',
        'shared_media_url': 'https://scontent.cdninstagram.com/v/t51.2885-15/'
        '90697930_220393875685423_3218385085483800637_n.jpg?stp=dst-jpg_'
        's160x160&_nc_cat=103&ccb=1-7&_nc_sid=5a057b&_nc_ohc=z194P_hvTg0AX-'
        '68NdR&_nc_ad=z-m&_nc_cid=0&_nc_ht=scontent.cdninstagram.com&oh=00_'
        'AfBhsQiBp9t6qiGma4pWTfN9zkcPJKUCYYlpBnY2BtOHoQ&oe=64505EFD&ig_cache_'
        'key=MjI3MjMxMzg3OTg1ODMxNTUzMg%3D%3D.2-ccb7-5',
        'username': 'ThisIsDFIR' }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
