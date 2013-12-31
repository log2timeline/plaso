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
"""Tests for the Google Chrome cookie parser."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import chrome_cookies as chrome_cookies_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import interface
from plaso.pvfs import utils

import pytz


class ChromeCookiesPluginTest(unittest.TestCase):
  """Tests for the Google Chrome cookie plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_plugin = chrome_cookies.ChromeCookiePlugin(pre_obj)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a Chrome cookie database and run a few tests."""
    test_file = os.path.join('test_data', 'cookies.db')

    events = None
    file_entry = utils.OpenOSFileEntry(test_file)
    with interface.SQLiteDatabase(file_entry) as database:
      generator = self.test_plugin.Process(database)
      self.assertTrue(generator)
      events = list(generator)

    # The cookie database contains 560 entries:
    #     560 creation timestamps.
    #     560 last access timestamps.
    #     560 expired timestamps.
    #      75 events created by Google Analytics cookies.
    # In total: 1755 events.
    self.assertEquals(len(events), 1755)

    # Check few "random" events to verify.
    linkedin_event = events[132]
    rubi_event = events[410]
    romney_event = events[475]
    auto_event = events[1495]
    utmz_event = events[837]
    utmb_event = events[520]
    utma_event = events[962]

    # Check the linkedin cookie.
    self.assertEquals(linkedin_event.timestamp_desc,
                      eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEquals(linkedin_event.host, 'www.linkedin.com')
    self.assertEquals(linkedin_event.cookie_name, 'leo_auth_token')
    self.assertFalse(linkedin_event.httponly)
    self.assertEquals(linkedin_event.url, 'http://www.linkedin.com/')

    # date -u -d"2011-08-25T21:50:27.292367+00:00" +"%s.%N"
    self.assertEquals(linkedin_event.timestamp, 1314309027292367)

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         linkedin_event)

    expected_msg = (
        u'http://www.linkedin.com/ (leo_auth_token) Flags: [HTTP only] = False '
        u'[Persistent] = True')

    self.assertEquals(msg, expected_msg)
    self.assertEquals(msg_short, u'www.linkedin.com (leo_auth_token)')

    self.assertEquals(rubi_event.timestamp_desc,
                      eventdata.EventTimestamp.ACCESS_TIME)

    # date -u -d"2012-04-01T13:54:34.949210+00:00" +"%s.%N"
    self.assertEquals(rubi_event.timestamp, 1333288474949210)

    self.assertEquals(rubi_event.url, 'http://rubiconproject.com/')
    self.assertEquals(rubi_event.path, '/')
    self.assertFalse(rubi_event.secure)
    self.assertTrue(rubi_event.persistent)

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         rubi_event)

    expected_msg = (
        u'http://rubiconproject.com/ (put_2249) Flags: [HTTP only] = False '
        u'[Persistent] = True')

    self.assertEquals(msg, expected_msg)

    self.assertEquals(
        romney_event.path,
        u'/2012/03/21/romney-tries-to-clean-up-etch-a-sketch-mess/')
    self.assertEquals(romney_event.host, 'politicalticker.blogs.cnn.com')

    # date -u -d"2012-03-22T01:47:21.012022+00:00" +"%s.%N"
    self.assertEquals(romney_event.timestamp, 1332380841012022)

    # date -u -d"2012-04-01T13:52:56.189444+00:00" +"%s.%N"
    self.assertEquals(auto_event.timestamp, 1333288376189444)
    self.assertEquals(auto_event.host, 'marvel.com')
    self.assertEquals(auto_event.cookie_name, 'autologin[timeout]')
    self.assertEquals(auto_event.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)
    # This particular cookie value represents a timeout value that corresponds
    # to the expiration date of the cookie.
    self.assertEquals(auto_event.data, u'1364824322')

    self.assertTrue(u'Keywords used to find site. = enders game' in
                    utmz_event.extra)
    self.assertEquals(utmz_event.domain_hash, u'68898382')
    self.assertEquals(utmz_event.sessions, 1)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         utmz_event)

    expected_msg = (
        u'http://imdb.com/ (__utmz) Flags: [HTTP only] = False [Persistent] = '
        u'True (GA analysis: Sessions: 1 - Domain Hash: 68898382 - '
        u'Sources: 1 - Variables: Last source used to access. = google Ad '
        u'campaign information. = (organic) Last type of visit. = organic '
        u'Keywords used to find site. = enders game)')
    self.assertEquals(msg, expected_msg)

    # Check the UTMA Google Analytics event.
    self.assertEquals(utma_event.timestamp_desc, 'Analytics Previous Time')
    self.assertEquals(utma_event.cookie_name, '__utma')
    self.assertEquals(utma_event.visitor_id, u'1827102436')
    self.assertEquals(utma_event.sessions, 2)
    # date -u -d"2012-03-22T01:55:29+00:00" +"%s.%N"
    self.assertEquals(utma_event.timestamp, 1332381329000000)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         utma_event)

    expected_msg = (
        u'http://assets.tumblr.com/ (__utma) Flags: [HTTP only] = False '
        u'[Persistent] = True (GA analysis: Sessions: 2 - Domain Hash: '
        u'151488169 - Visitor ID: 151488169)')
    self.assertEquals(msg, expected_msg)

    # Check the UTMB Google Analytics event.
    self.assertEquals(utmb_event.timestamp_desc,
                      eventdata.EventTimestamp.LAST_VISITED_TIME)
    self.assertEquals(utmb_event.cookie_name, '__utmb')
    self.assertEquals(utmb_event.domain_hash, u'154523900')
    self.assertEquals(utmb_event.pages_viewed, 1)
    # date -u -d"2012-03-22T01:48:30+00:00" +"%s.%N"
    self.assertEquals(utmb_event.timestamp, 1332380910000000)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         utmb_event)

    expected_msg = (
        u'http://upressonline.com/ (__utmb) Flags: [HTTP only] = False '
        u'[Persistent] = True (GA analysis: Pages Viewed: 1 - Domain Hash: '
        u'154523900)')
    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
