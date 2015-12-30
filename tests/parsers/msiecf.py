#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

from plaso.formatters import msiecf as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import msiecf

from tests.parsers import test_lib


class MsiecfParserTest(test_lib.ParserTestCase):
  """Tests for the MSIE Cache Files (MSIECF) parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = msiecf.MsiecfParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'index.dat'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 32768 bytes
    #   Number of items                 : 7
    #   Number of recovered items       : 11

    # 7 + 11 records, each with 4 records.
    self.assertEqual(len(event_objects), (7 + 11) * 4)

    # Record type             : URL
    # Offset range            : 21376 - 21632 (256)
    # Location                : Visited: testing@http://www.trafficfusionx.com
    #                           /download/tfscrn2/funnycats.exe
    # Primary time            : Jun 23, 2011 18:02:10.066000000
    # Secondary time          : Jun 23, 2011 18:02:10.066000000
    # Expiration time         : Jun 29, 2011 17:55:02
    # Last checked time       : Jun 23, 2011 18:02:12
    # Cache directory index   : -2 (0xfe)

    event_object = event_objects[8]
    expected_url = (
        u'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
        u'/funnycats.exe')

    self.assertEqual(event_object.data_type, u'msiecf:url')
    self.assertEqual(event_object.offset, 21376)
    self.assertEqual(event_object.url, expected_url)
    self.assertEqual(event_object.cache_directory_index, -2)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:10.066')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)

    event_object = event_objects[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:10.066')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)

    event_object = event_objects[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-29 17:55:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.EXPIRATION_TIME)

    event_object = event_objects[11]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-06-23 18:02:12')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_CHECKED_TIME)

    expected_msg = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/funnycats.exe '
        u'Number of hits: 6 '
        u'Cached file size: 0')
    expected_msg_short = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/fun...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # Test file with leak and redirected records.
    test_file = self._GetTestFilePath([u'nfury_index.dat'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # MSIE Cache File information:
    #   Version                         : 5.2
    #   File size                       : 491520 bytes
    #   Number of items                 : 1027
    #   Number of recovered items       : 8

    self.assertEqual(len(event_objects), 2898)

    event_object = event_objects[3]

    # Test cached file path.
    self.assertEqual(event_object.data_type, u'msiecf:url')

    expected_msg = (
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
    expected_msg_short = (
        u'Location: http://col.stc.s-msn.com/br/gbl/lg/csl/favicon.ico '
        u'Cached file: R6Q...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[21]
    expected_url = (
        u'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        u'pc=[TPAS_ID];ord=2642102')

    event_object = event_objects[16]

    self.assertEqual(event_object.data_type, u'msiecf:leak')
    self.assertEqual(event_object.timestamp, 0)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.NOT_A_TIME)
    self.assertEqual(event_object.cache_directory_index, 1)
    self.assertEqual(event_object.cache_directory_name, u'VUQHQA73')
    self.assertEqual(event_object.cached_file_size, 1966)
    self.assertEqual(event_object.cached_filename, u'ADSAdClient31[1].htm')
    self.assertEqual(event_object.recovered, False)

    expected_msg = (
        u'Cached file: VUQHQA73\\ADSAdClient31[1].htm '
        u'Cached file size: 1966')
    expected_msg_short = (
        u'Cached file: VUQHQA73\\ADSAdClient31[1].htm')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[21]
    expected_url = (
        u'http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;sz=1x1;'
        u'pc=[TPAS_ID];ord=2642102')

    self.assertEqual(event_object.data_type, u'msiecf:redirected')
    self.assertEqual(event_object.timestamp, 0)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.NOT_A_TIME)
    self.assertEqual(event_object.url, expected_url)
    self.assertEqual(event_object.recovered, False)

    expected_msg = u'Location: {0:s}'.format(expected_url)
    expected_msg_short = (
        u'Location: http://ad.doubleclick.net/ad/N2724.Meebo/B5343067.13;'
        u'sz=1x1;pc=[TPA...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
