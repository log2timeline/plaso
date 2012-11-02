#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
import pytz

from plaso.lib import putils
from plaso.parsers import syslog


class EmptyObject(object):
  """An empty object to store preprocessing information."""


class SyslogUnitTest(unittest.TestCase):
  """A unit test for the timelib."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = os.path.join('plaso/test_data')
    file_path = os.path.join(self.base_path, 'syslog')
    self.filehandle = putils.OpenOSFile(file_path)

  def testParsing(self):
    """Test parsing of a syslog file."""
    pre = EmptyObject()
    pre.zone = pytz.UTC
    sl = syslog.ParseSyslog(pre)

    self.filehandle.seek(0)
    sl_generator = sl.Parse(self.filehandle)

    events = list(sl_generator)
    first = events[0]

    self.assertEquals(first.timestamp, 1327218753000000)
    self.assertEquals(first.hostname, 'myhostname.myhost.com')
    self.assertEquals(first.description_long, (('[client, pid: 30840] : '
                                                'INFO No new content.')))

    self.assertEquals(len(events), 12)

    self.assertEquals(events[10].description_long, ('[aprocess, pid: 101001] '
                                                    ': This is a multi-line '
                                                    'message that screws up'
                                                    'many syslog parsers.'))

if __name__ == '__main__':
  unittest.main()
