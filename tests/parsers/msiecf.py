#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import msiecf

from tests.parsers import test_lib


class MSIECFParserTest(test_lib.ParserTestCase):
  """Tests for the MSIE Cache Files (MSIECF) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile(['index.dat'], parser)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 32768 bytes
    #   Number of items                 : 7
    #   Number of recovered items       : 11

    # 7 + 11 records, each with 4 records.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, (7 + 11) * 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Record type             : URL
    # Offset range            : 21376 - 21632 (256)
    # Location                : Visited: testing@http://www.trafficfusionx.com
    #                           /download/tfscrn2/funnycats.exe
    # Primary time            : Jun 23, 2011 18:02:10.066000000
    # Secondary time          : Jun 23, 2011 18:02:10.066000000
    # Expiration time         : Jun 29, 2011 17:55:02
    # Last checked time       : Jun 23, 2011 18:02:12
    # Cache directory index   : -2 (0xfe)

    expected_event_values = {
        'cache_directory_index': -2,
        'cached_file_size': 0,
        'data_type': 'msiecf:url',
        'date_time': '2011-06-23 18:02:10.0660000',
        'number_of_hits': 6,
        'offset': 21376,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'url': (
            'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
            '/funnycats.exe')}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'data_type': 'msiecf:url',
        'date_time': '2011-06-23 18:02:10.0660000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    expected_event_values = {
        'data_type': 'msiecf:url',
        'date_time': '2011-06-29 17:55:02',
        'timestamp_desc': definitions.TIME_DESCRIPTION_EXPIRATION}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_event_values = {
        'data_type': 'msiecf:url',
        'date_time': '2011-06-23 18:02:12',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_CHECKED}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

  def testParseLeakAndRedirect(self):
    """Tests the Parse function with leak and redirected records."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile(['nfury_index.dat'], parser)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 491520 bytes
    #   Number of items                 : 1027
    #   Number of recovered items       : 8

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2898)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'cache_directory_index': 0,
        'cache_directory_name': 'R6QWCVX4',
        'cached_file_size': 4286,
        'cached_filename': 'favicon[1].ico',
        'data_type': 'msiecf:url',
        'date_time': '2010-11-10 07:54:32',
        'http_headers': (
            'HTTP/1.1 200 OK\r\n'
            'Content-Type: image/x-icon\r\n'
            'ETag: "0922651f38cb1:0",\r\n'
            'X-Powered-By: ASP.NET\r\n'
            'P3P: CP="BUS CUR CONo FIN IVDo ONL OUR PHY SAMo TELo"\r\n'
            'Content-Length: 4286\r\n'
            '\r\n'
            '~U:nfury\r\n'),
        'number_of_hits': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_CHECKED,
        'url': 'http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'cache_directory_index': 1,
        'cache_directory_name': 'VUQHQA73',
        'cached_file_size': 1966,
        'cached_filename': 'ADSAdClient31[1].htm',
        'data_type': 'msiecf:leak',
        'date_time': 'Not set',
        'recovered': False,
        'timestamp_desc': definitions.TIME_DESCRIPTION_NOT_A_TIME}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)

    expected_event_values = {
        'data_type': 'msiecf:redirected',
        'date_time': 'Not set',
        'recovered': False,
        'timestamp_desc': definitions.TIME_DESCRIPTION_NOT_A_TIME,
        'url': (
            'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;'
            'sz=1x1;pc=[TPAS_ID];ord=2642102')}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile(
        ['MSHist012013031020130311-index.dat'], parser,
        timezone='Europe/Amsterdam')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 83)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Test primary last visited time, in UTC, event.
    expected_event_values = {
        'date_time': '2013-03-10 10:18:17.2810000',
        'timestamp': '2013-03-10 10:18:17.281000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'url': ':2013031020130311: -@:Host: libmsiecf.googlecode.com'}

    self.CheckEventValues(storage_writer, events[80], expected_event_values)

    # Test secondary last visited time, in local time, event.
    expected_event_values = {
        'date_time': '2013-03-10 11:18:17.2810000',
        'timestamp': '2013-03-10 10:18:17.281000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'url': ':2013031020130311: -@:Host: libmsiecf.googlecode.com'}

    self.CheckEventValues(storage_writer, events[81], expected_event_values)

    # Test last checked time event.
    expected_event_values = {
        'date_time': '2013-03-10 10:18:18',
        'timestamp': '2013-03-10 10:18:18.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_CHECKED,
        'url': ':2013031020130311: -@:Host: libmsiecf.googlecode.com'}

    self.CheckEventValues(storage_writer, events[82], expected_event_values)


if __name__ == '__main__':
  unittest.main()
