#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Firefox cache files parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox_cache as _  # pylint: disable=unused-import
from plaso.lib import errors
from plaso.parsers import firefox_cache

from tests.parsers import test_lib


class FirefoxCacheParserTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCacheParser."""

  def testParseCache_InvalidFile(self):
    """Verify that parser do not accept small, invalid files."""
    parser = firefox_cache.FirefoxCacheParser()
    path_segments = ['firefox_cache', 'invalid_file']

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(path_segments, parser)

  def testParseCache_001(self):
    """Test Firefox 28 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile([
        'firefox_cache', 'firefox28', '_CACHE_001_'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1668)

    events = list(storage_writer.GetEvents())

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2014-04-21 14:13:35.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.url, 'HTTP:http://start.ubuntu.com/12.04/sprite.png')

    expected_message = (
        'Fetched 2 time(s) '
        '[HTTP/1.0 200 OK] GET '
        '"HTTP:http://start.ubuntu.com/12.04/sprite.png"')
    expected_short_message = (
        '[HTTP/1.0 200 OK] GET '
        '"HTTP:http://start.ubuntu.com/12.04/sprite.png"')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.version, "1.19")

  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_002_'], parser)

    expected_url = (
        'HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
        '1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
        'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
        'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
        'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
        'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
        '2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
        '%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~')

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 141)

    events = list(storage_writer.GetEvents())

    event = events[5]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.url, expected_url)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2014-04-21 14:10:58.000000')

    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.version, "1.19")

  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[7]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_url = (
        'HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/'
        'jquery.min.js')
    self.assertEqual(event_data.url, expected_url)

    self.CheckTimestamp(event.timestamp, '2014-04-21 14:11:07.000000')

    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.version, "1.19")

  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', 'E8D65m01'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_001_'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 73)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-05-02 14:15:03.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Fetched 1 time(s) '
        '[HTTP/1.1 200 OK] GET '
        '"HTTP:http://start.mozilla.org/en-US/"')
    expected_short_message = (
        '[HTTP/1.1 200 OK] GET '
        '"HTTP:http://start.mozilla.org/en-US/"')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_002_'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2014-05-02 14:25:55.000000')

  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2014-05-02 14:15:07.000000')


class FirefoxCache2ParserTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCache2Parser."""

  def testParseCache2Entry(self):
    """Test Firefox cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2',
        '1F4B3A4FC81FB19C530758231FA54313BE8F6FA2']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-05-02 15:35:31.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_url = (
        ':https://tiles.cdn.mozilla.net/images/'
        '8acf9436e1b315f5f04b9435a518bcd1aef131f8.5663.png')
    self.assertEqual(event_data.url, expected_url)

    self.assertEqual(event_data.request_method, 'GET')
    self.assertEqual(event_data.response_code, 'HTTP/1.1 200 OK')
    self.assertEqual(event_data.fetch_count, 2)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-05-02 15:35:31.000000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2016-05-01 15:35:31.000000')

  def testParseInvalidCache2Entry(self):
    """Test file with valid filename and invalid content."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2',
        'C966EB70794E44E7E3E8A260106D0C72439AF65B']

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(path_segments, parser)


if __name__ == '__main__':
  unittest.main()
