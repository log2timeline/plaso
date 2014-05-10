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
"""Tests for Firefox cache files parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import firefox_cache as firefox_cache_formatter
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers import firefox_cache as firefox_cache_parser
from plaso.parsers import test_lib

__author__ = 'Petter Bjelland (petter.bjelland@gmail.com)'


class FirefoxCacheTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCacheParser."""

  def setUp(self):
    pre_obj = event.PreprocessObject()
    self._parser = firefox_cache_parser.FirefoxCacheParser(pre_obj)

  def VerifyMajorMinor(self, events):
    """Verify that valid Firefox cahce version is extracted."""
    for event_object in events:
      self.assertEquals(event_object.major, 1)
      self.assertEquals(event_object.minor, 19)

  def testParseCache_InvalidFile(self):
    """Verify that parser do not accept small, invalid files."""

    test_file = self._GetTestFilePath(['firefox_cache', 'invalid_file'])

    event_generator = self._ParseFile(self._parser, test_file)

    self.assertRaises(errors.UnableToParseFile,
        self._GetEventObjects, (event_generator))

  def testParseCache_001(self):
    """Test Firefox 28 cache file _CACHE_001_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox28',
        '_CACHE_001_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(574, len(event_objects))
    self.assertEquals(event_objects[1].url,
        'HTTP:http://start.ubuntu.com/12.04/sprite.png')

    self.assertEquals(event_objects[1].timestamp,
        timelib_test.CopyStringToTimestamp('2014-04-21 14:13:35'))

    self.VerifyMajorMinor(event_objects)

    expected_msg = (
      u'Fetched 2 time(s) '
      u'[HTTP/1.0 200 OK] GET '
      u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')
    expected_msg_short = (
      u'[HTTP/1.0 200 OK] GET '
      u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')

    self._TestGetMessageStrings(event_objects[1],
        expected_msg, expected_msg_short)

  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox28',
        '_CACHE_002_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(58, len(event_objects))
    self.assertEquals(event_objects[2].url,
        ('HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
         '1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
         'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
         'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
         'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
         'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
         '2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
         '%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~'))

    self.assertEquals(event_objects[1].timestamp,
        timelib_test.CopyStringToTimestamp('2014-04-21 14:10:58'))

    self.VerifyMajorMinor(event_objects)

  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox28',
        '_CACHE_003_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(4, len(event_objects))

    self.assertEquals(event_objects[3].url,
        'HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js')

    self.assertEquals(event_objects[3].timestamp,
        timelib_test.CopyStringToTimestamp('2014-04-21 14:11:07'))

    self.VerifyMajorMinor(event_objects)

  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox28',
        'E8D65m01'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(4, len(event_objects))

  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox3',
        '_CACHE_001_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(25, len(event_objects))

    self.assertEquals(event_objects[0].timestamp,
        timelib_test.CopyStringToTimestamp('2014-05-02 14:15:03'))

    expected_msg = (
      u'Fetched 1 time(s) '
      u'[HTTP/1.1 200 OK] GET '
      u'"HTTP:http://start.mozilla.org/en-US/"')
    expected_msg_short = (
      u'[HTTP/1.1 200 OK] GET '
      u'"HTTP:http://start.mozilla.org/en-US/"')

    self._TestGetMessageStrings(event_objects[0],
        expected_msg, expected_msg_short)

  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox3',
        '_CACHE_002_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(3, len(event_objects))

    self.assertEquals(event_objects[1].timestamp,
        timelib_test.CopyStringToTimestamp('2014-05-02 14:25:55'))

  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""

    test_file = self._GetTestFilePath(['firefox_cache', 'firefox3',
        '_CACHE_003_'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(2, len(event_objects))

    self.assertEquals(event_objects[1].timestamp,
        timelib_test.CopyStringToTimestamp('2014-05-02 14:15:07'))

if __name__ == '__main__':
  unittest.main()
