#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the default plist plugin."""

from __future__ import unicode_literals

import datetime
import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import default

from tests.parsers.plist_plugins import test_lib

import pytz  # pylint: disable=wrong-import-order


class TestDefaultPlist(test_lib.PlistPluginTestCase):
  """Tests for the default plist plugin."""

  def testProcessSingle(self):
    """Tests Process on a plist containing a root, value and timestamp."""
    top_level_dict_single = {
        'DE-00-AD-00-BE-EF': {
            'Name': 'DBF Industries Slideshow Lazer', 'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.UTC)}}

    plugin = default.DefaultPlugin()
    storage_writer = self._ParsePlistWithPlugin(
        plugin, 'single', top_level_dict_single)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-11-02 01:21:38.997672')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.root, '/DE-00-AD-00-BE-EF')
    self.assertEqual(event_data.key, 'LastUsed')

    expected_string = (
        '/DE-00-AD-00-BE-EF/LastUsed')

    self._TestGetMessageStrings(
        event_data, expected_string, expected_string)

  def testProcessMulti(self):
    """Tests Process on a plist containing five keys with date values."""
    top_level_dict_many_keys = {
        'DeviceCache': {
            '44-00-00-00-00-04': {
                'Name': 'Apple Magic Trackpad 2', 'LMPSubversion': 796,
                'LMPVersion': 3, 'PageScanMode': 0, 'ClassOfDevice': 9620,
                'SupportedFeatures': b'\x00\x00\x00\x00', 'Manufacturer': 76,
                'PageScanPeriod': 0, 'ClockOffset': 17981, 'LastNameUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.UTC),
                'InquiryRSSI': 198, 'PageScanRepetitionMode': 1,
                'LastServicesUpdate':
                datetime.datetime(2012, 11, 2, 1, 13, 23, tzinfo=pytz.UTC),
                'displayName': 'Apple Magic Trackpad 2', 'LastInquiryUpdate':
                datetime.datetime(
                    2012, 11, 2, 1, 13, 17, 324095, tzinfo=pytz.UTC),
                'Services': '', 'BatteryPercent': 0.61},
            '44-00-00-00-00-02': {
                'Name': 'test-macpro', 'ClockOffset': 28180,
                'ClassOfDevice': 3670276, 'PageScanMode': 0,
                'LastNameUpdate': datetime.datetime(
                    2011, 4, 7, 17, 56, 53, 524275, tzinfo=pytz.UTC),
                'PageScanPeriod': 2, 'PageScanRepetitionMode': 1,
                'LastInquiryUpdate': datetime.datetime(
                    2012, 7, 10, 22, 5, 0, 20116, tzinfo=pytz.UTC)}}}

    plugin = default.DefaultPlugin()
    storage_writer = self._ParsePlistWithPlugin(
        plugin, 'nested', top_level_dict_many_keys)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2011-04-07 17:56:53.524275')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.root, '/DeviceCache/44-00-00-00-00-02')
    self.assertEqual(event_data.key, 'LastNameUpdate')


if __name__ == '__main__':
  unittest.main()
