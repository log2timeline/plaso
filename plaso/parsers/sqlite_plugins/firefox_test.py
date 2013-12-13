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
"""Tests for the Mozilla Firefox history parser."""
import collections
import os
import unittest

from plaso.formatters import firefox
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import firefox
from plaso.parsers.sqlite_plugins import interface

import pytz


class FirefoxHistoryPluginTest(unittest.TestCase):
  """Tests for the Mozilla Firefox history parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

    self.test_parser = firefox.FirefoxHistoryPlugin(pre_obj)

  def testParseFile(self):
    """Read a Firefox History file and run a few tests."""
    test_file = os.path.join('test_data', 'places.sqlite')

    events = None
    with open(test_file, 'rb') as file_object:
      with interface.SQLiteDatabase(file_object) as database:
        generator = self.test_parser.Process(database)
        self.assertTrue(generator)
        events = list(generator)

    # The places.sqlite file contains 205 events (1 page visit,
    # 2 x 91 bookmark records, 2 x 3 bookmark annotations,
    # 2 x 8 bookmark folders).
    self.assertEquals(len(events), 205)

    # Check the first page visited event.
    event_object = events[0]

    self.assertEquals(event_object.data_type, 'firefox:places:page_visited')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.PAGE_VISITED)

    # date -u -d"2011-07-01 11:16:21.371935" +"%s.%N"
    self.assertEquals(event_object.timestamp,
                      (1309518981 * 1000000) + (371935000 / 1000))

    expected_url = 'http://news.google.com/'
    self.assertEquals(event_object.url, expected_url)

    expected_title = 'Google News'
    self.assertEquals(event_object.title, expected_title)

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
         u'%s (%s) [count: 1] Host: news.google.com '
         u'(URL not typed directly) Transition: TYPED') % (
         expected_url, expected_title)

    self.assertEquals(msg, expected_msg)

    # Check the first bookmark event.
    event_object = events[1]

    self.assertEquals(event_object.data_type, 'firefox:places:bookmark')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.ADDED_TIME)

    self.assertEquals(event_object.timestamp, 1309518839266344)

    # Check the second bookmark event.
    event_object = events[2]

    self.assertEquals(event_object.data_type, 'firefox:places:bookmark')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)

    self.assertEquals(event_object.timestamp, 1309518839267198)

    expected_url = (
        'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
        'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark%2F'
        'feedURI&maxResults=10&queryType=1')
    self.assertEquals(event_object.url, expected_url)

    expected_title = 'Recently Bookmarked'
    self.assertEquals(event_object.title, expected_title)

    # Test the event specific formatter.
    msg, dummy_msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
         u'Bookmark URL %s (%s) [folder=BOOKMARKS_MENU&'
         u'folder=UNFILED_BOOKMARKS&folder=TOOLBAR&sort=12&excludeQueries=1&'
         u'excludeItemIfParentHasAnnotation=livemark%%2FfeedURI&maxResults=10&'
         u'queryType=1] visit count 0') % (
         expected_title, expected_url)

    self.assertEquals(msg, expected_msg)

    # Check the first bookmark annotation event.
    event_object = events[183]

    self.assertEquals(event_object.data_type,
                     'firefox:places:bookmark_annotation')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    self.assertEquals(event_object.timestamp, 1309518839267146)

    # Check the second bookmark annotation event.
    event_object = events[184]

    self.assertEquals(event_object.data_type,
                      'firefox:places:bookmark_annotation')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)

    self.assertEquals(event_object.timestamp, 0)

    expected_url = (
        'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
        'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark%2F'
        'feedURI&maxResults=10&queryType=1')
    self.assertEquals(event_object.url, expected_url)

    expected_title = 'Recently Bookmarked'
    self.assertEquals(event_object.title, expected_title)

    # Test the event specific formatter.
    msg, dummy_msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
         u'Bookmark Annotation: [RecentlyBookmarked] to bookmark [%s] (%s)') % (
         expected_title, expected_url)

    self.assertEquals(msg, expected_msg)

    # Check the second last bookmark folder event.
    event_object = events[203]

    self.assertEquals(event_object.data_type, 'firefox:places:bookmark_folder')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.ADDED_TIME)

    self.assertEquals(event_object.timestamp, 1300701901553774)

    # Check the last bookmark folder event.
    event_object = events[204]

    self.assertEquals(event_object.data_type, 'firefox:places:bookmark_folder')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)

    self.assertEquals(event_object.timestamp, 1309518851766851)

    expected_title = 'Latest Headlines'
    self.assertEquals(event_object.title, expected_title)

    # Test the event specific formatter.
    msg, dummy_msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = u'%s' % expected_title

    self.assertEquals(msg, expected_msg)

  def testAnotherFile(self):
    """Test another FF file."""
    test_file = os.path.join('test_data', 'places_new.sqlite')

    events = None
    with open(test_file, 'rb') as file_object:
      with interface.SQLiteDatabase(file_object) as database:
        generator = self.test_parser.Process(database)
        self.assertTrue(generator)
        events = list(generator)

    # The places.sqlite file contains 84 events:
    #     34 page visits.
    #     28 bookmarks
    #     14 bookmark folders
    #     8 annotations
    self.assertEquals(len(events), 84)
    c = collections.Counter()
    for e in events:
      c[e.data_type] += 1

    self.assertEquals(c['firefox:places:bookmark'], 28)
    self.assertEquals(c['firefox:places:page_visited'], 34)
    self.assertEquals(c['firefox:places:bookmark_folder'], 14)
    self.assertEquals(c['firefox:places:bookmark_annotation'], 8)

    random_event = events[10]
    # 2013-10-30T21:57:11.281942+00:00.
    self.assertEquals(random_event.timestamp, 1383170231281942)

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        random_event)

    self.assertEquals(msg_short, u'URL: http://code.google.com/p/plaso')
    expected_msg = (
        u'http://code.google.com/p/plaso [count: 1] Host: code.google.com '
        '(URL not typed directly) Transition: TYPED')

    self.assertEquals(msg, expected_msg)


class FirefoxDownloadsPluginTest(unittest.TestCase):
  """Tests for the Mozilla Firefox downloads parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

    self.test_parser = firefox.FirefoxDownloadsPlugin(pre_obj)

  def testParseFile(self):
    """Read a Firefox History file and run a few tests."""
    test_file = os.path.join('test_data', 'downloads.sqlite')

    events = None
    with open(test_file, 'rb') as file_object:
      with interface.SQLiteDatabase(file_object) as database:
        generator = self.test_parser.Process(database)
        self.assertTrue(generator)
        events = list(generator)

    # The downloads.sqlite file contains 2 events (1 donwloads)
    self.assertEquals(len(events), 2)

    # Check the first page visited event.
    event_object = events[0]

    self.assertEquals(event_object.data_type, 'firefox:downloads:download')

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.START_TIME)

    self.assertEquals(event_object.timestamp, 1374173999312000)

    expected_url = ('https://plaso.googlecode.com/files/'
                    'plaso-static-1.0.1-win32-vs2008.zip')
    self.assertEquals(event_object.url, expected_url)

    expected_full_path = ('file:///D:/plaso-static-1.0.1-win32-vs2008.zip')
    self.assertEquals(event_object.full_path, expected_full_path)

    self.assertEquals(event_object.received_bytes, 15974599)
    self.assertEquals(event_object.total_bytes, 15974599)


if __name__ == '__main__':
  unittest.main()
