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

import StringIO
import unittest

from plaso.lib import event
from plaso.output import l2t_csv
from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2


class L2tCsvTest(unittest.TestCase):
  source_short_map = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      'SourceShort'].values:
    source_short_map[value.name] = value.number

  def setUp(self):
    self.output = StringIO.StringIO()
    self.formatter = l2t_csv.L2tCsv(self.output)

  def testStart(self):
    correct_line = ('date,time,timezone,MACB,source,sourcetype,type,user,host,'
                    'short,desc,version,filename,inode,notes,format,extra\n')

    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), correct_line)

  def CreateProto(self, an_event):
    """Return a protobuf object."""
    proto = plaso_storage_pb2.EventObject()
    for attr in an_event.GetAttributes():
      if attr == 'source_short':
        proto.source_short = self.source_short_map.get(an_event.source_short, 6)
      elif attr == 'pathspec':
        path = transmission_pb2.PathSpec()
        path.ParseFromString(an_event.pathspec)
        proto.pathspec.MergeFrom(path)
      elif hasattr(proto, attr):
        attribute_value = getattr(an_event, attr)
        if type(attribute_value) == str:
          attribute_value = attribute_value.decode('utf8', 'ignore')
        setattr(proto, attr, attribute_value)
      else:
        a = proto.attributes.add()
        a.key = attr
        a.value = getattr(an_event, attr)
    return proto

  def testEventBody(self):
    """Test ensures that returned lines returned are fmt CSV as expected."""
    evt = event.EventObject()
    evt.timestamp = 1340821021000000
    evt.timestamp_desc = 'Entry Written'
    evt.source_short = 6
    evt.source_long = 'Syslog'
    evt.hostname = 'ubuntu'
    evt.display_name = 'log/syslog.1'
    evt.description_short = ('Reporter <CRON> PID: 8442 (pam_unix(cron:session)'
                             ': session\n closed for user root)')
    evt.description_long = ('Reporter <CRON> PID: 8442 (pam_unix(cron:session)'
                            ':session closed for user root)')
    self.formatter.EventBody(self.CreateProto(evt))
    correct = ('06/27/2012,18:17:01,UTC,....,LOG,Syslog,Entry '
               'Written,-,ubuntu,Reporter <CRON> PID: 8442 '
               '(pam_unix(cron:session): session closed for user '
               'root),Reporter <CRON> PID: 8442 (pam_unix(cron:session):'
               'session closed for user root),2,log/syslog.1,-,-,-,\n')
    self.assertEquals(self.output.getvalue(), correct)

  def testEventBodyNoCommas(self):
    """Test ensures that commas inside fields are replaced by space."""
    evt = event.EventObject()
    evt.timestamp = 1340821021000000
    evt.timestamp_desc = 'Entry,Written'
    evt.source_short = 6
    evt.source_long = 'Syslog'
    evt.hostname = 'ubuntu'
    evt.display_name = 'log/syslog.1'
    evt.description_short = ('Reporter,<CRON>,PID:,8442 (pam_unix(cron:session)'
                             ': session closed for user root)')
    evt.description_long = ('Reporter,<CRON>,PID:,8442 (pam_unix(cron:session)'
                            ':session closed for user root)')
    self.formatter.EventBody(self.CreateProto(evt))
    correct = ('06/27/2012,18:17:01,UTC,....,LOG,Syslog,Entry '
               'Written,-,ubuntu,Reporter <CRON> PID: 8442 '
               '(pam_unix(cron:session): session closed for user '
               'root),Reporter <CRON> PID: 8442 (pam_unix(cron:session):'
               'session closed for user root),2,log/syslog.1,-,-,-,\n')
    self.assertEquals(self.output.getvalue(), correct)


if __name__ == '__main__':
  unittest.main()
