#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Firefox cache files parser."""

import unittest

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

    self.assertEqual(storage_writer.number_of_events, 1668)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-04-21 14:13:35',
        'fetch_count': 2,
        'request_method': 'GET',
        'response_code': 'HTTP/1.0 200 OK',
        'url': 'HTTP:http://start.ubuntu.com/12.04/sprite.png',
        'version': '1.19'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_002_'], parser)

    self.assertEqual(storage_writer.number_of_events, 141)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'url': (
            'HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
            '1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
            'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
            'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
            'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
            'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
            '2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
            '%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~')}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-04-21 14:10:58'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.version, '1.19')

  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_events, 9)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-04-21 14:11:07',
        'url': (
             'HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/'
             'jquery.min.js')}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.version, '1.19')

  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', 'E8D65m01'], parser)

    self.assertEqual(storage_writer.number_of_events, 9)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_001_'], parser)

    self.assertEqual(storage_writer.number_of_events, 73)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-05-02 14:15:03',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': 'HTTP:http://start.mozilla.org/en-US/'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_002_'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-05-02 14:25:55'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_003_'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2014-05-02 14:15:07'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)


class FirefoxCache2ParserTest(test_lib.ParserTestCase):
  """A unit test for the FirefoxCache2Parser."""

  def testParseCache2Entry(self):
    """Test Firefox cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', '1F4B3A4FC81FB19C530758231FA54313BE8F6FA2']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_events, 3)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2015-05-02 15:35:31',
        'fetch_count': 2,
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': (
            ':https://tiles.cdn.mozilla.net/images/'
            '8acf9436e1b315f5f04b9435a518bcd1aef131f8.5663.png')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2015-05-02 15:35:31'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'date_time': '2016-05-01 15:35:31'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testParseInvalidCache2Entry(self):
    """Test file with valid filename and invalid content."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', 'C966EB70794E44E7E3E8A260106D0C72439AF65B']

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(path_segments, parser)


if __name__ == '__main__':
  unittest.main()
