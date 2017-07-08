#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

from plaso.formatters import msiecf  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import msiecf

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MSIECFParserTest(test_lib.ParserTestCase):
  """Tests for the MSIE Cache Files (MSIECF) parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'index.dat'])
  def testParse(self):
    """Tests the Parse function."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile([u'index.dat'], parser)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 32768 bytes
    #   Number of items                 : 7
    #   Number of recovered items       : 11

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
        u'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
        u'/funnycats.exe')

    self.assertEqual(event.data_type, u'msiecf:url')
    self.assertEqual(event.offset, 21376)
    self.assertEqual(event.url, expected_url)
    self.assertEqual(event.cache_directory_index, -2)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:10.066')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    event = events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:10.066')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    event = events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-29 17:55:02')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)

    event = events[11]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:12')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_CHECKED)

    expected_message = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/funnycats.exe '
        u'Number of hits: 6 '
        u'Cached file size: 0')
    expected_short_message = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/fun...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'nfury_index.dat'])
  def testParseLeakAndRedirect(self):
    """Tests the Parse function with leak and redirected records."""
    parser = msiecf.MSIECFParser()
    storage_writer = self._ParseFile([u'nfury_index.dat'], parser)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 491520 bytes
    #   Number of items                 : 1027
    #   Number of recovered items       : 8

    self.assertEqual(storage_writer.number_of_events, 2898)

    events = list(storage_writer.GetEvents())

    event = events[3]

    # Test cached file path.
    self.assertEqual(event.data_type, u'msiecf:url')

    expected_message = (
        u'Location: http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico '
        u'Number of hits: 1 '
        u'Cached file: R6QWCVX4\\favicon[1].ico '
        u'Cached file size: 4286 '
        u'HTTP headers: HTTP/1.1 200 OK - '
        u'Content-Type: image/x-icon - '
        u'ETag: "0922651f38cb1:0", - '
        u'X-Powered-By: ASP.NET - P3P: '
        u'CP="BUS CUR CONo FIN IVDo ONL OUR PHY SAMo TELo" - '
        u'Content-Length: 4286 - '
        u' - ~U:nfury - ')
    expected_short_message = (
        u'Location: http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico '
        u'Cached file: R6Q...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[21]
    expected_url = (
        u'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        u'pc=[TPAS_ID];ord=2642102')

    event = events[16]

    self.assertEqual(event.data_type, u'msiecf:leak')
    self.assertEqual(event.timestamp, 0)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    self.assertEqual(event.cache_directory_index, 1)
    self.assertEqual(event.cache_directory_name, u'VUQHQA73')
    self.assertEqual(event.cached_file_size, 1966)
    self.assertEqual(event.cached_filename, u'ADSAdClient31[1].htm')
    self.assertEqual(event.recovered, False)

    expected_message = (
        u'Cached file: VUQHQA73\\ADSAdClient31[1].htm '
        u'Cached file size: 1966')
    expected_short_message = (
        u'Cached file: VUQHQA73\\ADSAdClient31[1].htm')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[21]
    expected_url = (
        u'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        u'pc=[TPAS_ID];ord=2642102')

    self.assertEqual(event.data_type, u'msiecf:redirected')
    self.assertEqual(event.timestamp, 0)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    self.assertEqual(event.url, expected_url)
    self.assertEqual(event.recovered, False)

    expected_message = u'Location: {0:s}'.format(expected_url)
    expected_short_message = (
        u'Location: http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;'
        u'sz=1x1;pc=[TPA...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
