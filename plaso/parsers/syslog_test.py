#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a unit test for the syslog parser in plaso."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import syslog as syslog_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import syslog
from plaso.parsers import test_lib

import pytz


class SyslogUnitTest(unittest.TestCase):
  """A unit test for the timelib."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.year = 2012
    pre_obj.zone = pytz.UTC
    self._parser = syslog.SyslogParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'syslog')

    events = test_lib.ParseFile(self._parser, test_file)

    # TODO let's add code to convert Jan 22 2012 07:52:33 into the
    # corresponding timestamp, I think that will be more readable
    self.assertEquals(events[0].timestamp, 1327218753000000)
    self.assertEquals(events[0].hostname, 'myhostname.myhost.com')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(events[0])
    self.assertEquals(
        msg, '[client, pid: 30840] : INFO No new content.')

    self.assertEquals(len(events), 13)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(events[11])
    self.assertEquals(msg, (
        '[aprocess, pid: 101001] : This is a multi-line message that screws up'
        'many syslog parsers.'))

    # Mon Feb 29 01:15:43 UTC 2012.
    self.assertEquals(events[6].timestamp, 1330478143000000)

    # Sat Mar 23 23:01:18 UTC 2013 - testing year increment.
    self.assertEquals(events[8].timestamp, 1364079678000000)


if __name__ == '__main__':
  unittest.main()
