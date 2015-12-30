#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the default plist plugin."""

import datetime
import unittest

from plaso.formatters import plist as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.plist_plugins import default

from tests.parsers.plist_plugins import test_lib

import pytz


class TestDefaultPlist(test_lib.PlistPluginTestCase):
  """Tests for the default plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = default.DefaultPlugin()

  def testProcessSingle(self):
    """Tests Process on a plist containing a root, value and timestamp."""
    top_level_dict_single = {
        u'DE-00-AD-00-BE-EF': {
            u'Name': u'DBF Industries Slideshow Lazer', u'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.UTC)}}

    event_object_generator = self._ParsePlistWithPlugin(
        self._plugin, u'single', top_level_dict_single)
    event_objects = self._GetEventObjectsFromQueue(event_object_generator)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-02 01:21:38.997672')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.root, u'/DE-00-AD-00-BE-EF')
    self.assertEqual(event_object.key, u'LastUsed')

    expected_string = (
        u'/DE-00-AD-00-BE-EF/LastUsed')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

  def testProcessMulti(self):
    """Tests Process on a plist containing five keys with date values."""
    top_level_dict_many_keys = {
        u'DeviceCache': {
            u'44-00-00-00-00-04': {
                u'Name': u'Apple Magic Trackpad 2', u'LMPSubversion': 796,
                u'LMPVersion': 3, u'PageScanMode': 0, u'ClassOfDevice': 9620,
                u'SupportedFeatures': b'\x00\x00\x00\x00', u'Manufacturer': 76,
                u'PageScanPeriod': 0, u'ClockOffset': 17981, u'LastNameUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.UTC),
                u'InquiryRSSI': 198, u'PageScanRepetitionMode': 1,
                u'LastServicesUpdate':
                datetime.datetime(2012, 11, 2, 1, 13, 23, tzinfo=pytz.UTC),
                u'displayName': u'Apple Magic Trackpad 2', u'LastInquiryUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 13, 17, 324095, tzinfo=pytz.UTC),
                u'Services': u'', u'BatteryPercent': 0.61},
            u'44-00-00-00-00-02': {
                u'Name': u'test-macpro', u'ClockOffset': 28180,
                u'ClassOfDevice': 3670276, u'PageScanMode': 0,
                u'LastNameUpdate': datetime.datetime(
                    2011, 4, 7, 17, 56, 53, 524275, tzinfo=pytz.UTC),
                u'PageScanPeriod': 2, u'PageScanRepetitionMode': 1,
                u'LastInquiryUpdate': datetime.datetime(
                    2012, 7, 10, 22, 5, 0, 20116, tzinfo=pytz.UTC)}}}

    event_queue_consumer = self._ParsePlistWithPlugin(
        self._plugin, u'nested', top_level_dict_many_keys)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 5)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-04-07 17:56:53.524275')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.root, u'/DeviceCache/44-00-00-00-00-02')
    self.assertEqual(event_object.key, u'LastNameUpdate')


if __name__ == '__main__':
  unittest.main()
