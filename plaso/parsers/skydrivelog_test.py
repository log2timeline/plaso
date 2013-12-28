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
"""This file contains a unit test for the skydrivelog parser in plaso."""

import os
import pytz
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import skydrivelog as skydrivelog_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import skydrivelog as skydrivelog_parser
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogUnitTest(unittest.TestCase):
  """A unit test for the SkyDriveLog Parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.timezone('UTC')
    self._parser = skydrivelog_parser.SkyDriveLogParser(pre_obj, None)

  def _TestText(self, evt, text):
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(evt)
    self.assertEquals(msg, text)

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'skydrive.log')

    events = test_lib.ParseFile(self._parser, test_file)

    self.assertEquals(len(events), 18)

    # expr `date -u -d "2013-08-01 21:22:28.999" +"%s%N"` \/ 1000
    self.assertEquals(events[0].timestamp, 1375392148999000)
    # expr `date -u -d "2013-08-01 21:22:29.702" +"%s%N"` \/ 1000
    self.assertEquals(events[1].timestamp, 1375392149702000)
    self.assertEquals(events[2].timestamp, 1375392149702000)
    self.assertEquals(events[3].timestamp, 1375392149702000)
    # expr `date -u -d "2013-08-01 21:22:58.344 " +"%s%N"` \/ 1000
    self.assertEquals(events[4].timestamp, 1375392178344000)
    self.assertEquals(events[5].timestamp, 1375392178344000)

    self._TestText(events[0],
      u'[global.cpp:626!logVersionInfo] (DETAIL) 17.0.2011.0627 (Ship)')

    self._TestText(events[3], (
      u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
      u'103%3bLR%3d12345678905623%3aEP%3d2'))

    self._TestText(events[17],
      u'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!')


if __name__ == '__main__':
  unittest.main()
