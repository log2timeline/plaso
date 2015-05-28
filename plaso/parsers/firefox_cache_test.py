# -*- coding: utf-8 -*-
"""Tests for Firefox cache files parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import firefox_cache as firefox_cache_formatter
from plaso.lib import errors
from plaso.lib import timelib_test
from plaso.lib import timelib
from plaso.parsers import firefox_cache
from plaso.parsers import test_lib


__author__ = 'Petter Bjelland (petter.bjelland@gmail.com)'


class FirefoxOldCacheTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxOldCacheParser."""

  def setUp(self):
    """Create parser."""

    self._parser = firefox_cache.FirefoxOldCacheParser()

  def VerifyMajorMinor(self, events):
    """Verify that valid Firefox cache version is extracted."""
    for event_object in events:
      self.assertEquals(event_object.major, 1)
      self.assertEquals(event_object.minor, 19)

  def testParseCache_InvalidFile(self):
    """Verify that parser do not accept small, invalid files."""

    test_file = self._GetTestFilePath([u'firefox_cache', u'invalid_file'])

    with self.assertRaises(errors.UnableToParseFile):
      _ = self._ParseFile(self._parser, test_file)

  def testParseCache_001(self):
    """Test Firefox 28 cache file _CACHE_001_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox28', u'_CACHE_001_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(1665, len(event_objects))
    self.assertEquals(
        event_objects[3].url, u'HTTP:http://start.ubuntu.com/12.04/sprite.png')

    self.assertEquals(
        event_objects[3].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-04-21 14:13:35'))

    self.VerifyMajorMinor(event_objects)

    expected_msg = (
        u'Fetched 2 time(s) '
        u'[HTTP/1.0 200 OK] GET '
        u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')
    expected_msg_short = (
        u'[HTTP/1.0 200 OK] GET '
        u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')

    self._TestGetMessageStrings(
        event_objects[3], expected_msg, expected_msg_short)

  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox28', u'_CACHE_002_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(141, len(event_objects))
    self.assertEquals(
        event_objects[5].url,
        (u'HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
         u'1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
         u'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
         u'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
         u'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
         u'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
         u'2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
         u'%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~'))

    self.assertEquals(
        event_objects[1].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-04-21 14:10:58'))

    self.VerifyMajorMinor(event_objects)

  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox28', u'_CACHE_003_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(9, len(event_objects))

    self.assertEquals(
        event_objects[7].url,
        u'HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/'
        u'jquery.min.js')

    self.assertEquals(
        event_objects[7].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-04-21 14:11:07'))

    self.VerifyMajorMinor(event_objects)

  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox28', u'E8D65m01'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(9, len(event_objects))

  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox3', u'_CACHE_001_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(73, len(event_objects))

    self.assertEquals(
        event_objects[0].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-05-02 14:15:03'))

    expected_msg = (
        u'Fetched 1 time(s) '
        u'[HTTP/1.1 200 OK] GET '
        u'"HTTP:http://start.mozilla.org/en-US/"')
    expected_msg_short = (
        u'[HTTP/1.1 200 OK] GET '
        u'"HTTP:http://start.mozilla.org/en-US/"')

    self._TestGetMessageStrings(
        event_objects[0], expected_msg, expected_msg_short)

  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox3', u'_CACHE_002_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(6, len(event_objects))

    self.assertEquals(
        event_objects[2].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-05-02 14:25:55'))

  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'firefox3', u'_CACHE_003_'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(6, len(event_objects))

    self.assertEquals(
        event_objects[3].timestamp,
        timelib.Timestamp.CopyFromString(u'2014-05-02 14:15:07'))


class FirefoxCacheTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCacheParser."""

  def setUp(self):
    """Create parser."""

    self._parser = firefox_cache.FirefoxCacheParser()

  def testParseCache2Entry(self):
    """Test Firefox cache2 file parsing."""

    test_file = self._GetTestFilePath(
        [u'firefox_cache', u'cache2',
         u'1F4B3A4FC81FB19C530758231FA54313BE8F6FA2'])

    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(3, len(event_objects))

    self.assertEquals(
        event_objects[0].timestamp,
        timelib.Timestamp.CopyFromString(u'2015-05-02 15:35:31'))

    expected_last_modified = (
        timelib.Timestamp.CopyFromString(u'2015-05-02 15:35:31'))
    expected_expire_time = (
        timelib.Timestamp.CopyFromString(u'2016-05-01 15:35:31'))

    self.assertEquals(event_objects[1].timestamp, expected_last_modified)
    self.assertEquals(event_objects[2].timestamp, expected_expire_time)

    self.assertEquals(
        event_objects[0].url,
        u':https://tiles.cdn.mozilla.net/images/'
        u'8acf9436e1b315f5f04b9435a518bcd1aef131f8.5663.png')

    self.assertEquals(event_objects[0].request_method, u'GET')
    self.assertEquals(event_objects[0].response_code, u'HTTP/1.1 200 OK')
    self.assertEquals(event_objects[0].fetch_count, 2)

  def testParseInvalidCache2Entry(self):
    """Test file with valid filename and invalid content."""

    test_file = self._GetTestFilePath([
        u'firefox_cache', u'cache2',
        u'C966EB70794E44E7E3E8A260106D0C72439AF65B'])

    with self.assertRaises(errors.UnableToParseFile):
      _ = self._ParseFile(self._parser, test_file)


if __name__ == '__main__':
  unittest.main()
