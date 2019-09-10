#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msiecf as _  # pylint: disable=unused-import
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # 7 + 11 records, each with 4 records.
    self.assertEqual(storage_writer.number_of_events, (7 + 11) * 4)

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

    event = events[8]
    expected_url = (
        'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
        '/funnycats.exe')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'msiecf:url')
    self.assertEqual(event_data.offset, 21376)
    self.assertEqual(event_data.url, expected_url)
    self.assertEqual(event_data.cache_directory_index, -2)

    self.CheckTimestamp(event.timestamp, '2011-06-23 18:02:10.066000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    event = events[9]

    self.CheckTimestamp(event.timestamp, '2011-06-23 18:02:10.066000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    event = events[10]

    self.CheckTimestamp(event.timestamp, '2011-06-29 17:55:02.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)

    event = events[11]

    self.CheckTimestamp(event.timestamp, '2011-06-23 18:02:12.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_CHECKED)

    expected_message = (
        'Location: Visited: testing@http://www.trafficfusionx.com/download'
        '/tfscrn2/funnycats.exe '
        'Number of hits: 6 '
        'Cached file size: 0')
    expected_short_message = (
        'Location: Visited: testing@http://www.trafficfusionx.com/download'
        '/tfscrn2/fun...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseLeakAndRedirect(self):
    """Tests the Parse function with leak and redirected records."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile(['nfury_index.dat'], parser)
    self.assertEqual(storage_writer.number_of_warnings, 0)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 491520 bytes
    #   Number of items                 : 1027
    #   Number of recovered items       : 8

    self.assertEqual(storage_writer.number_of_events, 2898)

    events = list(storage_writer.GetEvents())

    event = events[3]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # Test cached file path.
    self.assertEqual(event_data.data_type, 'msiecf:url')

    expected_message = (
        'Location: http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico '
        'Number of hits: 1 '
        'Cached file: R6QWCVX4\\favicon[1].ico '
        'Cached file size: 4286 '
        'HTTP headers: HTTP/1.1 200 OK - '
        'Content-Type: image/x-icon - '
        'ETag: "0922651f38cb1:0", - '
        'X-Powered-By: ASP.NET - P3P: '
        'CP="BUS CUR CONo FIN IVDo ONL OUR PHY SAMo TELo" - '
        'Content-Length: 4286 - '
        ' - ~U:nfury - ')
    expected_short_message = (
        'Location: http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico '
        'Cached file: R6Q...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[21]
    expected_url = (
        'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        'pc=[TPAS_ID];ord=2642102')

    event = events[16]

    self.assertEqual(event.timestamp, 0)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'msiecf:leak')
    self.assertEqual(event_data.cache_directory_index, 1)
    self.assertEqual(event_data.cache_directory_name, 'VUQHQA73')
    self.assertEqual(event_data.cached_file_size, 1966)
    self.assertEqual(event_data.cached_filename, 'ADSAdClient31[1].htm')
    self.assertEqual(event_data.recovered, False)

    expected_message = (
        'Cached file: VUQHQA73\\ADSAdClient31[1].htm '
        'Cached file size: 1966')
    expected_short_message = (
        'Cached file: VUQHQA73\\ADSAdClient31[1].htm')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[21]
    self.assertEqual(event.timestamp, 0)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'msiecf:redirected')
    expected_url = (
        'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        'pc=[TPAS_ID];ord=2642102')
    self.assertEqual(event_data.url, expected_url)
    self.assertEqual(event_data.recovered, False)

    expected_message = 'Location: {0:s}'.format(expected_url)
    expected_short_message = (
        'Location: http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;'
        'sz=1x1;pc=[TPA...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
