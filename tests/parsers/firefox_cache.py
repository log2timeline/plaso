# -*- coding: utf-8 -*-
"""Tests for Firefox cache files parser."""

import unittest

from plaso.formatters import firefox_cache  # pylint: disable=unused-import
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import firefox_cache

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Petter Bjelland (petter.bjelland@gmail.com)'


class FirefoxCacheParserTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCacheParser."""

  def _VerifyMajorMinor(self, events):
    """Verify that valid Firefox cache version is extracted."""
    for event in events:
      self.assertEqual(event.major, 1)
      self.assertEqual(event.minor, 19)

  @shared_test_lib.skipUnlessHasTestFile([u'firefox_cache', u'invalid_file'])
  def testParseCache_InvalidFile(self):
    """Verify that parser do not accept small, invalid files."""
    parser = firefox_cache.FirefoxCacheParser()
    path_segments = [u'firefox_cache', u'invalid_file']

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(path_segments, parser)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox28', u'_CACHE_001_'])
  def testParseCache_001(self):
    """Test Firefox 28 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox28', u'_CACHE_001_'], parser)

    self.assertEqual(storage_writer.number_of_events, 1665)

    events = list(storage_writer.GetEvents())

    event = events[3]
    self.assertEqual(
        event.url, u'HTTP:http://start.ubuntu.com/12.04/sprite.png')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-04-21 14:13:35')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Fetched 2 time(s) '
        u'[HTTP/1.0 200 OK] GET '
        u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')
    expected_short_message = (
        u'[HTTP/1.0 200 OK] GET '
        u'"HTTP:http://start.ubuntu.com/12.04/sprite.png"')

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

    self._VerifyMajorMinor(events)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox28', u'_CACHE_002_'])
  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox28', u'_CACHE_002_'], parser)

    expected_url = (
        u'HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
        u'1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
        u'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
        u'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
        u'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
        u'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
        u'2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
        u'%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~')

    self.assertEqual(storage_writer.number_of_events, 141)

    events = list(storage_writer.GetEvents())

    event = events[5]
    self.assertEqual(event.url, expected_url)

    event = events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-04-21 14:10:58')
    self.assertEqual(event.timestamp, expected_timestamp)

    self._VerifyMajorMinor(events)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox28', u'_CACHE_003_'])
  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox28', u'_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[7]
    expected_url = (
        u'HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/'
        u'jquery.min.js')
    self.assertEqual(event.url, expected_url)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-04-21 14:11:07')
    self.assertEqual(event.timestamp, expected_timestamp)

    self._VerifyMajorMinor(events)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox28', u'E8D65m01'])
  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox28', u'E8D65m01'], parser)

    self.assertEqual(storage_writer.number_of_events, 9)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox3', u'_CACHE_001_'])
  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox3', u'_CACHE_001_'], parser)

    self.assertEqual(storage_writer.number_of_events, 73)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-02 14:15:03')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Fetched 1 time(s) '
        u'[HTTP/1.1 200 OK] GET '
        u'"HTTP:http://start.mozilla.org/en-US/"')
    expected_short_message = (
        u'[HTTP/1.1 200 OK] GET '
        u'"HTTP:http://start.mozilla.org/en-US/"')

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox3', u'_CACHE_002_'])
  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox3', u'_CACHE_002_'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-02 14:25:55')
    self.assertEqual(event.timestamp, expected_timestamp)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'firefox3', u'_CACHE_003_'])
  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        [u'firefox_cache', u'firefox3', u'_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-02 14:15:07')
    self.assertEqual(event.timestamp, expected_timestamp)


class FirefoxCache2ParserTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCache2Parser."""

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'cache2', u'1F4B3A4FC81FB19C530758231FA54313BE8F6FA2'])
  def testParseCache2Entry(self):
    """Test Firefox cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        u'firefox_cache', u'cache2',
        u'1F4B3A4FC81FB19C530758231FA54313BE8F6FA2']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-05-02 15:35:31')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_url = (
        u':https://tiles.cdn.mozilla.net/images/'
        u'8acf9436e1b315f5f04b9435a518bcd1aef131f8.5663.png')
    self.assertEqual(event.url, expected_url)

    self.assertEqual(event.request_method, u'GET')
    self.assertEqual(event.response_code, u'HTTP/1.1 200 OK')
    self.assertEqual(event.fetch_count, 2)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-05-02 15:35:31')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-05-01 15:35:31')
    self.assertEqual(event.timestamp, expected_timestamp)

  @shared_test_lib.skipUnlessHasTestFile([
      u'firefox_cache', u'cache2', u'C966EB70794E44E7E3E8A260106D0C72439AF65B'])
  def testParseInvalidCache2Entry(self):
    """Test file with valid filename and invalid content."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        u'firefox_cache', u'cache2',
        u'C966EB70794E44E7E3E8A260106D0C72439AF65B']

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(path_segments, parser)


if __name__ == '__main__':
  unittest.main()
