#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the default plist plugin."""

import datetime
import unittest

from plaso.artifacts import knowledge_base
# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import context
from plaso.parsers.plist_plugins import default
from plaso.parsers.plist_plugins import test_lib

import pytz


class TestDefaultPlist(test_lib.PlistPluginTestCase):
  """Tests for the default plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = default.DefaultPlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._parser_context = context.ParserContext(knowledge_base_object)

  def testProcessSingle(self):
    """Tests Process on a plist containing a root, value and timestamp."""
    top_level_dict_single = {
        'DE-00-AD-00-BE-EF': {
            'Name': 'DBF Industries Slideshow Lazer', 'LastUsed':
            datetime.datetime(
                2012, 11, 2, 1, 21, 38, 997672, tzinfo=pytz.utc)}}

    events = list(self._plugin.Process(
        self._parser_context, plist_name='single',
        top_level=top_level_dict_single))
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    # Fri Nov  2 02:21:38.997672 CET 2012
    self.assertEquals(event_object.timestamp, 1351819298997672)
    self.assertEquals(event_object.root, u'/DE-00-AD-00-BE-EF')
    self.assertEquals(event_object.key, u'LastUsed')

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

    events = list(self._plugin.Process(
        self._parser_context, plist_name='nested',
        top_level=top_level_dict_many_keys))
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 5)

    event_object = event_objects[0]

    # Thu Apr  7 19:56:53.524275 CEST 2011
    self.assertEquals(event_object.timestamp, 1302199013524275)
    self.assertEquals(event_object.root, u'/DeviceCache/44-00-00-00-00-02')
    self.assertEquals(event_object.key, u'LastNameUpdate')


if __name__ == '__main__':
  unittest.main()
