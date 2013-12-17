#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a unit test for the selinux parser in plaso."""
import os
import unittest

from plaso.formatters import selinux
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import selinux
from plaso.pvfs import utils

import pytz

__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxUnitTest(unittest.TestCase):
  """A unit test for the selinux."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'selinux.log')
    self.filehandle = utils.OpenOSFile(test_file)

  def testParsing(self):
    """Test parsing of a selinux file."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.year = 2013
    pre_obj.zone = pytz.UTC
    sl = selinux.SELinuxParser(pre_obj, None)

    self.filehandle.seek(0)
    sl_generator = sl.Parse(self.filehandle)
    events = list(sl_generator)

    self.assertEquals(len(events), 4)

    normal_entry = events[0]
    short_date = events[1]
    no_msg = events[2]
    under_score = events[3]

    self.assertEquals(normal_entry.timestamp, 1337845201174000)
    self.assertEquals(short_date.timestamp, 1337845201000000)
    self.assertEquals(no_msg.timestamp, 1337845222174000)
    self.assertEquals(under_score.timestamp, 1337845666174000)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(normal_entry)
    self.assertEquals( msg, (
        '[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        'auid=4294967295 new auid=0 old ses=4294967295 new ses=1165'))

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(short_date)
    self.assertEquals(msg, (
        '[audit_type: SHORTDATE] check rounding'))

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(no_msg)
    self.assertEquals(msg, ('[audit_type: NOMSG]'))

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(under_score)
    self.assertEquals(msg, (
        '[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        'auid=4294967295 new auid=54321 old ses=4294967295 new ses=1166'))


if __name__ == '__main__':
  unittest.main()
