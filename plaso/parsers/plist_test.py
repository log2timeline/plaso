#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests the plist parser."""

import unittest

from plaso.parsers import manager
from plaso.parsers import plist
from plaso.parsers import test_lib


class PlistParserTest(test_lib.ParserTestCase):
  """Tests the plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    parser_filter_string = 'plist_bluetooth, plist_default'
    manager.ParsersManager.SetParserFilterString(parser_filter_string)
    self._parser = plist.PlistParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['plist_binary'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 12)

    timestamps, roots, keys = zip(
        *[(evt.timestamp, evt.root, evt.key) for evt in event_objects])

    expected_timestamps = frozenset([
        1345251192528750, 1351827808261762, 1345251268370453,
        1351818803000000, 1351819298997672, 1351818797324095,
        1301012201414766, 1302199013524275, 1341957900020116,
        1350666391557044, 1350666385239661, 1341957896010535])

    self.assertTrue(set(expected_timestamps) == set(timestamps))
    self.assertEquals(12, len(set(timestamps)))

    expected_roots = frozenset([
        '/DeviceCache/00-0d-fd-00-00-00',
        '/DeviceCache/44-00-00-00-00-00',
        '/DeviceCache/44-00-00-00-00-01',
        '/DeviceCache/44-00-00-00-00-02',
        '/DeviceCache/44-00-00-00-00-03',
        '/DeviceCache/44-00-00-00-00-04'])
    self.assertTrue(expected_roots == set(roots))
    self.assertEquals(6, len(set(roots)))

    expected_keys = frozenset([
        u'LastInquiryUpdate',
        u'LastServicesUpdate',
        u'LastNameUpdate'])
    self.assertTrue(expected_keys == set(keys))
    self.assertEquals(3, len(set(keys)))


if __name__ == '__main__':
  unittest.main()
