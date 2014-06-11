#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the Google Analytics cookies."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import ganalytics
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import firefox_cookies
from plaso.parsers.sqlite_plugins import test_lib


class GoogleAnalyticsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Analytics plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._pre_obj = event.PreprocessObject()

  def _GetAnalyticsCookies(self, generator):
    """Return a list of analytics cookies."""
    cookies = []
    for event_object in generator:
      if not hasattr(event_object, 'plugin'):
        continue
      if event_object.plugin.startswith('google_analytics'):
        cookies.append(event_object)

    return cookies

  def testParsingFirefox29CookieDatabase(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin(self._pre_obj)
    test_file = self._GetTestFilePath(['firefox_cookies.sqlite'])
    event_generator = self._ParseDatabaseFileWithPlugin(plugin, test_file)
    event_objects = self._GetAnalyticsCookies(event_generator)

    self.assertEquals(len(event_objects), 25)

    event_object = event_objects[14]

    self.assertEquals(
        event_object.utmcct,
        u'/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/')
    self.assertEquals(
        event_object.timestamp, timelib_test.CopyStringToTimestamp(
            '2013-10-30 21:56:06'))
    self.assertEquals(event_object.url, u'http://ads.aha.is/')
    self.assertEquals(event_object.utmcsr, u'mbl.is')

    expected_msg = (
        u'http://ads.aha.is/ (__utmz) Sessions: 1 Domain Hash: 137167072 '
        u'Sources: 1 Last source used to access: mbl.is Ad campaign '
        u'information: (referral) Last type of visit: referral Path to '
        u'the page of referring link: /frettir/erlent/2013/10/30/'
        u'maelt_med_kerfisbundnum_hydingum/')

    self._TestGetMessageStrings(
        event_object, expected_msg, u'http://ads.aha.is/ (__utmz)')

  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.ChromeCookiePlugin(self._pre_obj)
    test_file = self._GetTestFilePath(['cookies.db'])
    event_generator = self._ParseDatabaseFileWithPlugin(plugin, test_file)
    event_objects = self._GetAnalyticsCookies(event_generator)

    # The cookie database contains 560 entries in total. Out of them
    # there are 75 events created by the Google Analytics plugin.
    self.assertEquals(len(event_objects), 75)
    # Check few "random" events to verify.

    # Check an UTMZ Google Analytics event.
    event_object = event_objects[39]
    self.assertEquals(event_object.utmctr, u'enders game')
    self.assertEquals(event_object.domain_hash, u'68898382')
    self.assertEquals(event_object.sessions, 1)

    expected_msg = (
        u'http://imdb.com/ (__utmz) Sessions: 1 Domain Hash: 68898382 '
        u'Sources: 1 Last source used to access: google Ad campaign '
        u'information: (organic) Last type of visit: organic Keywords '
        u'used to find site: enders game')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'http://imdb.com/ (__utmz)')

    # Check the UTMA Google Analytics event.
    event_object = event_objects[41]
    self.assertEquals(event_object.timestamp_desc, u'Analytics Previous Time')
    self.assertEquals(event_object.cookie_name, u'__utma')
    self.assertEquals(event_object.visitor_id, u'1827102436')
    self.assertEquals(event_object.sessions, 2)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-03-22 01:55:29')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'http://assets.tumblr.com/ (__utma) Sessions: 2 Domain Hash: '
        u'151488169 Visitor ID: 151488169')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'http://assets.tumblr.com/ (__utma)')

    # Check the UTMB Google Analytics event.
    event_object = event_objects[34]
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)
    self.assertEquals(event_object.cookie_name, u'__utmb')
    self.assertEquals(event_object.domain_hash, u'154523900')
    self.assertEquals(event_object.pages_viewed, 1)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-03-22 01:48:30')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'http://upressonline.com/ (__utmb) Pages Viewed: 1 Domain Hash: '
        u'154523900')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'http://upressonline.com/ (__utmb)')


if __name__ == '__main__':
  unittest.main()
