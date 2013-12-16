#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a test for the default plist parser."""
import datetime
import unittest

from plaso.parsers.plist_plugins import default

import pytz


class TestDefaultPlist(unittest.TestCase):
  """The unit test for default plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.plugin = default.DefaultPlugin(None)

    self.top_level_dict_single = {
        'DE-00-AD-00-BE-EF': {
            'Name': 'DBF Industries Slideshow Lazer', 'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.utc)}}

    self.top_level_dict_many_keys = {
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

  def testDefault_single(self):
    """Ensure that the root, value, and timestamp are parsed correctly."""
    event = list(self.plugin.Process('single', self.top_level_dict_single))

    self.assertEquals(len(event), 1)
    self.assertEquals(event[0].root, '/DE-00-AD-00-BE-EF')
    self.assertEquals(event[0].key, 'LastUsed')
    self.assertEquals(event[0].timestamp, 1351819298997672)

  def testDefault_many_nested(self):
    """Test to ensure the five keys with dates values are yielded."""
    events = self.plugin.Process('nested', self.top_level_dict_many_keys)

    self.assertEquals(len(list(events)), 5)


if __name__ == '__main__':
  unittest.main()
