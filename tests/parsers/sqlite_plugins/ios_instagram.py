#!/usr/bin/env python3
"""Tests for the iOS Instagram SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_instagram

from tests.parsers.sqlite_plugins import test_lib


class IOSInstagramThreadsTest(test_lib.SQLitePluginTestCase):
    """Tests for the iOS Instagram SQLite database plugin."""

    def testProcess(self):
        """Test the Process function."""
        plugin = ios_instagram.IOSInstagramPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "9368974384.db"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 75)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "message": None,
            "sender_identifier": "9368974384",
            "sent_time": "2020-03-22T19:12:02.808456+00:00",
            "shared_media_identifier": None,
            "shared_media_url": None,
            "username": "ThisIsDFIR",
            "video_chat_call_identifier": "18135614113062170",
            "video_chat_title": "Video chat ended",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "message": (
                "Clicked over to Threads. I still do not understand why this app "
                "exists."
            ),
            "sender_identifier": "22824420",
            "sent_time": "2020-03-25T01:41:17.164115+00:00",
            "shared_media_identifier": None,
            "shared_media_url": None,
            "username": None,
            "video_chat_call_identifier": None,
            "video_chat_title": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "message": None,
            "sender_identifier": "9368974384",
            "sent_time": "2020-03-25T01:49:04.901623+00:00",
            "shared_media_identifier": "251704772664178",
            "shared_media_url": (
                "https://scontent.cdninstagram.com/v/t51.2885-15/"
                "90697930_220393875685423_3218385085483800637_n.jpg?"
                "stp=dst-jpg_s160x160&_nc_cat=103&ccb=1-7&_nc_sid=5a057b&"
                "_nc_ohc=z194P_hvTg0AX-68NdR&_nc_ad=z-m&_nc_cid=0&"
                "_nc_ht=scontent.cdninstagram.com&"
                "oh=00_AfBhsQiBp9t6qiGma4pWTfN9zkcPJKUCYYlpBnY2BtOHoQ&oe=64505EFD&"
                "ig_cache_key=MjI3MjMxMzg3OTg1ODMxNTUzMg%3D%3D.2-ccb7-5"
            ),
            "username": "ThisIsDFIR",
            "video_chat_call_identifier": None,
            "video_chat_title": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
