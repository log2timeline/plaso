#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the default plist plugin."""

import datetime
import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.plist_plugins import default

from tests.parsers.plist_plugins import test_lib

import pytz  # pylint: disable=wrong-import-order


class TestDefaultPlist(test_lib.PlistPluginTestCase):
  """Tests for the default plist plugin."""

  def testProcessSingle(self):
    """Tests Process on a plist containing a root, value and timestamp."""
    top_level_dict_single = {
        u'DE-00-AD-00-BE-EF': {
            u'Name': u'DBF Industries Slideshow Lazer', u'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.UTC)}}

    plugin = default.DefaultPlugin()
    storage_writer = self._ParsePlistWithPlugin(
        plugin, u'single', top_level_dict_single)

    self.assertEqual(storage_writer.number_of_events, 1)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-02 01:21:38.997672')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.root, u'/DE-00-AD-00-BE-EF')
    self.assertEqual(event.key, u'LastUsed')

    expected_string = (
        u'/DE-00-AD-00-BE-EF/LastUsed')

    self._TestGetMessageStrings(event, expected_string, expected_string)

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

    plugin = default.DefaultPlugin()
    storage_writer = self._ParsePlistWithPlugin(
        plugin, u'nested', top_level_dict_many_keys)

    self.assertEqual(storage_writer.number_of_events, 5)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-04-07 17:56:53.524275')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.root, u'/DeviceCache/44-00-00-00-00-02')
    self.assertEqual(event.key, u'LastNameUpdate')


if __name__ == '__main__':
  unittest.main()
