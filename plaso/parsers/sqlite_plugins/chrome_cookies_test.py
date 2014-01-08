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
"""Tests for the Google Chrome cookie database plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import chrome_cookies as chrome_cookies_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import interface
from plaso.parsers.sqlite_plugins import test_lib
from plaso.pvfs import utils

import pytz


class ChromeCookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome cookie database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._plugin = chrome_cookies.ChromeCookiePlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function on a Chrome cookie database file."""
    test_file = self._GetTestFilePath(['cookies.db'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The cookie database contains 560 entries:
    #     560 creation timestamps.
    #     560 last access timestamps.
    #     560 expired timestamps.
    #      75 events created by Google Analytics cookies.
    # In total: 1755 events.
    self.assertEquals(len(event_objects), 1755)

    # Check few "random" events to verify.

    # Check one linkedin cookie.
    event_object = event_objects[132]
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEquals(event_object.host, u'www.linkedin.com')
    self.assertEquals(event_object.cookie_name, u'leo_auth_token')
    self.assertFalse(event_object.httponly)
    self.assertEquals(event_object.url, u'http://www.linkedin.com/')

    # date -u -d"2011-08-25T21:50:27.292367+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1314309027292367)

    expected_msg = (
        u'http://www.linkedin.com/ (leo_auth_token) Flags: [HTTP only] = False '
        u'[Persistent] = True')
    expected_short = u'www.linkedin.com (leo_auth_token)'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check one of the visits to rubiconproject.com.
    event_object = event_objects[410]
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    # date -u -d"2012-04-01T13:54:34.949210+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1333288474949210)

    self.assertEquals(event_object.url, u'http://rubiconproject.com/')
    self.assertEquals(event_object.path, u'/')
    self.assertFalse(event_object.secure)
    self.assertTrue(event_object.persistent)

    expected_msg = (
        u'http://rubiconproject.com/ (put_2249) Flags: [HTTP only] = False '
        u'[Persistent] = True')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'rubiconproject.com (put_2249)')

    # Examine an event for a visit to a political blog site.
    event_object = event_objects[475]
    self.assertEquals(
        event_object.path,
        u'/2012/03/21/romney-tries-to-clean-up-etch-a-sketch-mess/')
    self.assertEquals(event_object.host, u'politicalticker.blogs.cnn.com')

    # date -u -d"2012-03-22T01:47:21.012022+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1332380841012022)

    # Examine a cookie that has an autologin entry.
    event_object = event_objects[1495]
    # date -u -d"2012-04-01T13:52:56.189444+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1333288376189444)
    self.assertEquals(event_object.host, u'marvel.com')
    self.assertEquals(event_object.cookie_name, u'autologin[timeout]')
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    # This particular cookie value represents a timeout value that corresponds
    # to the expiration date of the cookie.
    self.assertEquals(event_object.data, u'1364824322')

    # Check an UTMZ Google Analytics event.
    event_object = event_objects[837]
    self.assertTrue(u'Keywords used to find site. = enders game' in
                    event_object.extra)
    self.assertEquals(event_object.domain_hash, u'68898382')
    self.assertEquals(event_object.sessions, 1)

    expected_msg = (
        u'http://imdb.com/ (__utmz) Flags: [HTTP only] = False [Persistent] = '
        u'True (GA analysis: Sessions: 1 - Domain Hash: 68898382 - '
        u'Sources: 1 - Variables: Last source used to access. = google Ad '
        u'campaign information. = (organic) Last type of visit. = organic '
        u'Keywords used to find site. = enders game)')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'imdb.com (__utmz)')

    # Check the UTMA Google Analytics event.
    event_object = event_objects[962]
    self.assertEquals(event_object.timestamp_desc, u'Analytics Previous Time')
    self.assertEquals(event_object.cookie_name, u'__utma')
    self.assertEquals(event_object.visitor_id, u'1827102436')
    self.assertEquals(event_object.sessions, 2)
    # date -u -d"2012-03-22T01:55:29+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1332381329000000)

    expected_msg = (
        u'http://assets.tumblr.com/ (__utma) Flags: [HTTP only] = False '
        u'[Persistent] = True (GA analysis: Sessions: 2 - Domain Hash: '
        u'151488169 - Visitor ID: 151488169)')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'assets.tumblr.com (__utma)')

    # Check the UTMB Google Analytics event.
    event_object = event_objects[520]
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)
    self.assertEquals(event_object.cookie_name, u'__utmb')
    self.assertEquals(event_object.domain_hash, u'154523900')
    self.assertEquals(event_object.pages_viewed, 1)
    # date -u -d"2012-03-22T01:48:30+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1332380910000000)

    expected_msg = (
        u'http://upressonline.com/ (__utmb) Flags: [HTTP only] = False '
        u'[Persistent] = True (GA analysis: Pages Viewed: 1 - Domain Hash: '
        u'154523900)')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'upressonline.com (__utmb)')


if __name__ == '__main__':
  unittest.main()
