#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Tests for Java Cache IDX file parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import java_idx as java_idx_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import java_idx
from plaso.parsers import test_lib

import pytz


class IDXTest(test_lib.ParserTestCase):
  """Tests for Java Cache IDX file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._parser = java_idx.JavaIDXParser(pre_obj)

  def testParse602(self):
    """Tests the Parse function on a version 602 IDX file."""
    test_file = self._GetTestFilePath(['java_602.idx'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 2)

    event_object = event_container.events[0]

    idx_version_expected = 602
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = u'Unknown'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = u'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_object.url, url_expected)

    description_expected = u'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    last_modified_date_expected = 1273023259720 * 1000
    self.assertEqual(event_object.timestamp,
        last_modified_date_expected)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_container.events[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    # expr `date -u -d"2010-05-05T03:52:31+00:00" +"%s"` \* 1000000
    download_date_expected = 1273031551 * 1000000
    self.assertEqual(event_object.timestamp, download_date_expected)

  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    test_file = self._GetTestFilePath(['java.idx'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 2)

    event_object = event_container.events[0]

    idx_version_expected = 605
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = '10.7.119.10'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = (
        u'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        u'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_object.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    last_modified_date_expected = 996123600000 * 1000
    self.assertEqual(event_object.timestamp,
        last_modified_date_expected)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_container.events[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    download_date_expected = 1358094121 * 1000000
    self.assertEqual(event_object.timestamp, download_date_expected)


if __name__ == '__main__':
  unittest.main()
