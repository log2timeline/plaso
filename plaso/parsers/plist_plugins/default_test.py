#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the default plist plugin."""

import datetime
import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.lib import timelib_test
from plaso.parsers.plist_plugins import default
from plaso.parsers.plist_plugins import test_lib

import pytz


class TestDefaultPlist(test_lib.PlistPluginTestCase):
  """Tests for the default plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = default.DefaultPlugin()

  def testProcessSingle(self):
    """Tests Process on a plist containing a root, value and timestamp."""
    top_level_dict_single = {
        'DE-00-AD-00-BE-EF': {
            'Name': 'DBF Industries Slideshow Lazer', 'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.utc)}}

    event_object_generator = self._ParsePlistWithPlugin(
        self._plugin, 'single', top_level_dict_single)
    event_objects = self._GetEventObjectsFromQueue(event_object_generator)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-11-02 01:21:38.997672')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.root, u'/DE-00-AD-00-BE-EF')
    self.assertEqual(event_object.key, u'LastUsed')

    expected_string = (
        u'/DE-00-AD-00-BE-EF/LastUsed')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

  def testProcessMulti(self):
    """Tests Process on a plist containing five keys with date values."""
    top_level_dict_many_keys = {
        'DeviceCache': {
            '44-00-00-00-00-04': {
                'Name': 'Apple Magic Trackpad 2', 'LMPSubversion': 796,
                'LMPVersion': 3, 'PageScanMode': 0, 'ClassOfDevice': 9620,
                'SupportedFeatures': '\x00\x00\x00\x00', 'Manufacturer': 76,
                'PageScanPeriod': 0, 'ClockOffset': 17981, 'LastNameUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.utc),
                'InquiryRSSI': 198, 'PageScanRepetitionMode': 1,
                'LastServicesUpdate':
                datetime.datetime(2012, 11, 2, 1, 13, 23, tzinfo=pytz.utc),
                'displayName': 'Apple Magic Trackpad 2', 'LastInquiryUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 13, 17, 324095, tzinfo=pytz.utc),
                'Services': '', 'BatteryPercent': 0.61},
            '44-00-00-00-00-02': {
                'Name': 'test-macpro', 'ClockOffset': 28180, 'ClassOfDevice':
                3670276, 'PageScanMode': 0, 'LastNameUpdate':
                datetime.datetime(
                    2011, 4, 7, 17, 56, 53, 524275, tzinfo=pytz.utc),
                'PageScanPeriod': 2, 'PageScanRepetitionMode': 1,
                'LastInquiryUpdate':
                datetime.datetime(
                    2012, 7, 10, 22, 5, 0, 20116, tzinfo=pytz.utc)}}}

    event_queue_consumer = self._ParsePlistWithPlugin(
        self._plugin, 'nested', top_level_dict_many_keys)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 5)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-04-07 17:56:53.524275')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.root, u'/DeviceCache/44-00-00-00-00-02')
    self.assertEqual(event_object.key, u'LastNameUpdate')


if __name__ == '__main__':
  unittest.main()
