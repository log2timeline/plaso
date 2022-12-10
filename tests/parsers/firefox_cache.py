#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Firefox cache files parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import firefox_cache

from tests.parsers import test_lib


class FirefoxCacheParserTest(test_lib.ParserTestCase):
  """Tests for the Firefox cache version 1 file parser."""

  def testParseCache_InvalidFile(self):
    """Verify that parser do not accept small, invalid files."""
    parser = firefox_cache.FirefoxCacheParser()
    path_segments = ['firefox_cache', 'invalid_file']

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(path_segments, parser)

  def testParseCache_001(self):
    """Test Firefox 28 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile([
        'firefox_cache', 'firefox28', '_CACHE_001_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 575)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2014-07-03T02:24:30+00:00',
        'fetch_count': 2,
        'last_fetched_time': '2014-04-21T14:13:35+00:00',
        'last_modified_time': '2014-04-21T14:10:53+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.0 200 OK',
        'url': 'HTTP:http://start.ubuntu.com/12.04/sprite.png',
        'version': '1.19'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testParseCache_002(self):
    """Test Firefox 28 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_002_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 58)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': None,
        'fetch_count': 1,
        'last_fetched_time': '2014-04-21T14:10:58+00:00',
        'last_modified_time': '2014-04-21T14:10:59+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': (
            'HTTP:http://www.google-analytics.com/__utm.gif?utmwv=5.5.0&utms='
            '1&utmn=1106893631&utmhn=www.dagbladet.no&utmcs=windows-1252&ut'
            'msr=1920x1080&utmvp=1430x669&utmsc=24-bit&utmul=en-us&utmje=0&'
            'utmfl=-&utmdt=Dagbladet.no%20-%20forsiden&utmhid=460894302&utm'
            'r=-&utmp=%2F&utmht=1398089458997&utmac=UA-3072159-1&utmcc=__ut'
            'ma%3D68537988.718312608.1398089459.1398089459.1398089459.1%3B%'
            '2B__utmz%3D68537988.1398089459.1.1.utmcsr%3D(direct)%7Cutmccn'
            '%3D(direct)%7Cutmcmd%3D(none)%3B&aip=1&utmu=qBQ~'),
        'version': '1.19'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testParseCache_003(self):
    """Test Firefox 28 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', '_CACHE_003_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2015-04-15T01:02:45+00:00',
        'fetch_count': 3,
        'last_fetched_time': '2014-04-21T14:11:07+00:00',
        'last_modified_time': '2014-04-21T14:11:07+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': ('HTTP:https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/'
                'jquery.min.js'),
        'version': '1.19'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testParseAlternativeFilename(self):
    """Test Firefox 28 cache 003 file with alternative filename."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox28', 'E8D65m01'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': None,
        'fetch_count': 1,
        'last_fetched_time': '2014-04-21T14:10:55+00:00',
        'last_modified_time': '2014-04-21T14:10:56+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': ('HTTP~4294967294~0:https://sb-ssl.google.com/safebrowsing/'
                'newkey?client=Firefox&appver=28.0&pver=2.2'),
        'version': '1.19'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLegacyCache_001(self):
    """Test Firefox 3 cache file _CACHE_001_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_001_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2014-05-03T14:15:02+00:00',
        'fetch_count': 1,
        'last_fetched_time': '2014-05-02T14:15:03+00:00',
        'last_modified_time': '2014-05-02T14:15:03+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': 'HTTP:http://start.mozilla.org/en-US/',
        'version': '1.11'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLegacyCache_002(self):
    """Test Firefox 3 cache file _CACHE_002_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_002_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': None,
        'fetch_count': 1,
        'last_fetched_time': '2014-05-02T14:25:55+00:00',
        'last_modified_time': '2014-05-02T14:25:56+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': (
            'HTTP:http://pubads.g.doubleclick.net/gampad/ads?gdfp_req=1&correla'
            'tor=4077823583010238&output=json_html&callback=window.parent.googl'
            'etag.impl.pubads.setAdContentsBySlotForAsync&impl=fifs&json_a=1&sf'
            'v=1-0-0&iu_parts=8578%2Cdagbladet.no%2Cforside&enc_prev_ius=%2F0%2'
            'F1%2F2%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2'
            '%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2%2C%2F0%2F1%2F2%2C%2F'
            '0%2F1%2F2&prev_iu_szs=980x150%7C980x300%7C988x150%7C988x300%7C996x'
            '150%7C980x90%7C980x420%7C980x120%7C970x250%2C1920x1200%2C458x1000%'
            '7C268x1000%7C180x500%7C1x1%7C160x600%7C300x600%2C620x530%7C468x400'
            '%7C580x500%7C580x400%2C980x600%7C980x400%2C458x1000%7C268x1000%7C1'
            '80x500%7C1x1%7C160x600%7C300x600%2C268x1001%2C230x400%2C980x225%7C'
            '980x120%2C300x250&prev_scp=seqNo%3D1%7CseqNo%3D1%7CseqNo%3D1%7Cseq'
            'No%3D1%7CseqNo%3D1%7CseqNo%3D2%7CseqNo%3D2%7CseqNo%3D1%7CseqNo%3D1'
            '%7CseqNo%3D1&cust_params=inURL%3D%252F%26URLIs%3D%252F%26Query%3D%'
            '26Domain%3Dwww.dagbladet.no&cookie=ID%3D49f2358866de8ec4%3AT%3D139'
            '9040755%3AS%3DALNI_MbZadiDZK7K41FUWDO-8oTOKEM_qA&lmt=1399040752&dt'
            '=1399040755893&cc=100&biw=981&bih=524&oid=3&gut=v2&ifi=1&u_tz=-420'
            '&u_his=3&u_h=711&u_w=1137&u_ah=711&u_aw=1137&u_cd=24&u_nplug=1&u_n'
            'mime=1&flash=0&url=http%3A%2F%2Fwww.dagbladet.no%2F&adks=102621492'
            '7%2C1984650426%2C453428387%2C394044041%2C3551794028%2C453428390%2C'
            '119054132%2C1101158140%2C2808405456%2C2815534088&vrg=38&vrp=38&ga_'
            'vid=530740800.1399040756&ga_sid=1399040756&ga_hid=1397472294&ga_fc'
            '=true'),
        'version': '1.11'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLegacyCache_003(self):
    """Test Firefox 3 cache file _CACHE_003_ parsing."""
    parser = firefox_cache.FirefoxCacheParser()
    storage_writer = self._ParseFile(
        ['firefox_cache', 'firefox3', '_CACHE_003_'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2014-05-02T14:58:27+00:00',
        'fetch_count': 1,
        'last_fetched_time': '2014-05-02T14:15:07+00:00',
        'last_modified_time': '2014-05-02T14:15:08+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': ('HTTP:https://www.google-analytics.com/plugins/ga/'
                'inpage_linkid.js'),
        'version': '1.11'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


class FirefoxCache2ParserTest(test_lib.ParserTestCase):
  """Tests for the Firefox cache version 2 file parser."""

  def testParseCache2Entry(self):
    """Test Firefox cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', '1F4B3A4FC81FB19C530758231FA54313BE8F6FA2']
    storage_writer = self._ParseFile(path_segments, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2016-05-01T15:35:31+00:00',
        'fetch_count': 2,
        'last_fetched_time': '2015-05-02T15:35:31+00:00',
        'last_modified_time': '2015-05-02T15:35:31+00:00',
        'request_method': 'GET',
        'response_code': 'HTTP/1.1 200 OK',
        'url': (
            ':https://tiles.cdn.mozilla.net/images/'
            '8acf9436e1b315f5f04b9435a518bcd1aef131f8.5663.png'),
        'version': '2'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseInvalidCache2Entry(self):
    """Test file with valid filename and invalid content."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', 'C966EB70794E44E7E3E8A260106D0C72439AF65B']

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(path_segments, parser)

  def testParseVersion3Entry(self):
    """Test Firefox version 3 cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', '9E599395B8E39ED759C56FC9CD6BBD80FBB426DC']

    storage_writer = self._ParseFile(path_segments, parser)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2106-02-07T06:28:15+00:00',
        'fetch_count': 9,
        'last_fetched_time': '2021-07-18T02:52:12+00:00',
        'last_modified_time': '2021-07-18T02:52:12+00:00',
        'request_method': None,
        'response_code': None,
        'url': '~predictor-origin,:http://github.com/',
        'version': '2'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseVersion3Entry2(self):
    """Test Firefox version 3 cache2 file parsing."""
    parser = firefox_cache.FirefoxCache2Parser()
    path_segments = [
        'firefox_cache', 'cache2', '0EDDF8C091E2FED62E44BEDDDC1723F5BF38FE4F']

    storage_writer = self._ParseFile(path_segments, parser)

    expected_event_values = {
        'data_type': 'firefox:cache:record',
        'expiration_time': '2106-02-07T06:28:15+00:00',
        'fetch_count': 1,
        'last_fetched_time': '2021-08-07T22:42:42+00:00',
        'last_modified_time': '2021-08-07T22:42:44+00:00',
        'request_method': None,
        'response_code': None,
        'url': '~predictor-origin,:https://www.mozilla.org/',
        'version': '2'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
