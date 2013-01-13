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
"""Tests for plaso.output.l2t_csv."""
import re
import StringIO
import unittest

from plaso.lib import event
from plaso.lib import eventdata
from plaso.output import l2t_csv
from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2

__pychecker__ = 'no-funcdoc'


class DummyEventFormatter(eventdata.EventFormatter):
  """Implement a simple formatter for the events defined."""

  ID_RE = re.compile('UNKNOWN:Syslog:Entry', re.DOTALL)

  FORMAT_STRING = u'{text}'


class L2tCsvTest(unittest.TestCase):
  def setUp(self):
    self.output = StringIO.StringIO()
    self.formatter = l2t_csv.L2tCsv(self.output)

  def testStart(self):
    correct_line = ('date,time,timezone,MACB,source,sourcetype,type,user,host,'
                    'short,desc,version,filename,inode,notes,format,extra\n')

    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), correct_line)

  def testEventBody(self):
    """Test ensures that returned lines returned are fmt CSV as expected."""
    evt = event.EventObject()
    evt.timestamp = 1340821021000000
    evt.timestamp_desc = 'Entry Written'
    evt.source_short = 'LOG'
    evt.source_long = 'Syslog'
    evt.hostname = 'ubuntu'
    evt.filename = 'log/syslog.1'
    evt.text = (u'Reporter <CRON> PID: 8442 (pam_unix(cron:session)'
                ': session\n closed for user root)')

    self.formatter.EventBody(evt.ToProto())
    correct = ('06/27/2012,18:17:01,UTC,..C.,LOG,Syslog,Entry '
               'Written,-,ubuntu,Reporter <CRON> PID: 8442 '
               '(pam_unix(cron:session): session closed for user '
               'root),Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
               'session closed for user root),2,log/syslog.1,-,-,-,\n')
    self.assertEquals(self.output.getvalue(), correct)

  def testEventBodyNoCommas(self):
    """Test ensures that commas inside fields are replaced by space."""
    evt = event.EventObject()
    evt.timestamp = 1340821021000000
    evt.timestamp_desc = 'Entry,Written'
    evt.source_short = 'LOG'
    evt.source_long = 'Syslog'
    evt.hostname = 'ubuntu'
    evt.filename = 'log/syslog.1'
    evt.text = ('Reporter,<CRON>,PID:,8442 (pam_unix(cron:session)'
                ': session closed for user root)')

    self.formatter.EventBody(evt.ToProto())
    correct = ('06/27/2012,18:17:01,UTC,..C.,LOG,Syslog,Entry '
               'Written,-,ubuntu,Reporter <CRON> PID: 8442 '
               '(pam_unix(cron:session): session closed for user '
               'root),Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
               'session closed for user root),2,log/syslog.1,-,-,-,\n')
    self.assertEquals(self.output.getvalue(), correct)


if __name__ == '__main__':
  unittest.main()
