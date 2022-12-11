#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 18)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

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
        'access_time': None,
        'cache_directory_index': -2,
        'cached_file_size': 0,
        'creation_time': None,
        'data_type': 'msiecf:url',
        'expiration_time': '2011-06-29T17:55:02+00:00',
        'last_visited_time': '2011-06-23T18:02:10.0660000+00:00',
        'modification_time': None,
        'number_of_hits': 6,
        'offset': 21376,
        'primary_time': None,
        'recovered': False,
        'secondary_time': '2011-06-23T18:02:10.0660000+00:00',
        'synchronization_time': '2011-06-23T18:02:12+00:00',
        'url': (
            'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
            '/funnycats.exe')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLeakAndRedirect(self):
    """Tests the Parse function with leak and redirected records."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile(['nfury_index.dat'], parser)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 491520 bytes
    #   Number of items                 : 1027
    #   Number of recovered items       : 8

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1035)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2010-11-10T07:54:30.0920000+00:00',
        'cache_directory_index': 0,
        'cache_directory_name': 'R6QWCVX4',
        'cached_file_size': 4286,
        'cached_filename': 'favicon[1].ico',
        'creation_time': None,
        'data_type': 'msiecf:url',
        'expiration_time': '2011-09-13T21:36:18+00:00',
        'last_visited_time': None,
        'modification_time': '2010-08-10T00:03:00.0000000+00:00',
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
        'offset': 24576,
        'primary_time': None,
        'recovered': False,
        'secondary_time': None,
        'synchronization_time': '2010-11-10T07:54:32+00:00',
        'url': 'http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'cache_directory_index': 1,
        'cache_directory_name': 'VUQHQA73',
        'cached_file_size': 1966,
        'cached_filename': 'ADSAdClient31[1].htm',
        'data_type': 'msiecf:leak',
        'offset': 26368,
        'recovered': False}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'msiecf:redirected',
        'offset': 26880,
        'recovered': False,
        'url': (
            'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;'
            'sz=1x1;pc=[TPAS_ID];ord=2642102')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
