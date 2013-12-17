#!/usr/bin/python
# -*- coding: utf-8 -*-
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

"""Parser Test for Java Cache IDX files."""
import os
import unittest

from plaso.formatters import java_idx
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import java_idx
from plaso.pvfs import utils

import pytz


class IDXTest(unittest.TestCase):
  """The unit test for Java IDX parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self.test_parser = java_idx.JavaIDXParser(pre_obj)


  def testParseFile(self):
    """Read two Java IDX files and make few tests."""
    test_file = os.path.join('test_data', 'java.idx')

    events = None
    with utils.OpenOSFile(test_file) as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEqual(len(events), 2)

    event_object = events[0]
    idx_version_expected = 605
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = '10.7.119.10'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = (
        'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_object.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    last_modified_date_expected = 996123600000 * 1000
    self.assertEqual(event_object.timestamp,
        last_modified_date_expected)

    # Parse second event. Same metadata; different timestamp event.
    event_object = events[1]
    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    download_date_expected = 1358094121 * 1000000
    self.assertEqual(event_object.timestamp, download_date_expected)

    # Start testing 6.02 file.
    test_file = os.path.join('test_data', 'java_602.idx')
    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEqual(len(events), 2)

    event_object = events[0]
    idx_version_expected = 602
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = 'Unknown'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = 'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_object.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    last_modified_date_expected = 1273023259720 * 1000
    self.assertEqual(event_object.timestamp,
        last_modified_date_expected)

    # Parse second event. Same metadata; different timestamp event.
    event_object = events[1]
    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    # expr `date -u -d"2010-05-05T03:52:31+00:00" +"%s"` \* 1000000
    download_date_expected = 1273031551 * 1000000
    self.assertEqual(event_object.timestamp, download_date_expected)


if __name__ == '__main__':
  unittest.main()
