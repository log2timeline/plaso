#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the JSON output class."""

import StringIO
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import event
from plaso.lib import timelib_test
from plaso.output import json_out


class JsonTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2tjson'

  def __init__(self):
    """Initialize event with data."""
    super(JsonTestEvent, self).__init__()
    self.timestamp = timelib_test.CopyStringToTimestamp(
        '2012-06-27 18:17:01+00:00')
    self.hostname = u'ubuntu'
    self.display_name = u'OS: /var/log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=u'/cases/image.dd')
    self.pathspec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/var/log/syslog.1',
        parent=os_path_spec)


class JsonOutputTest(unittest.TestCase):
  """Tests for the JSON outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    self.output = StringIO.StringIO()
    self.formatter = json_out.Json(None, self.output)
    self.event_object = JsonTestEvent()

  def testStartAndEnd(self):
    """Test to ensure start and end functions do not add text."""
    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), u'')
    self.formatter.End()
    self.assertEquals(self.output.getvalue(), u'')

  def testEventBody(self):
    """Test ensures that returned lines returned are formatted as JSON."""

    expected_string = (
        '{{"username": "root", "display_name": "OS: /var/log/syslog.1", '
        '"uuid": "{0:s}", "data_type": "test:l2tjson", '
        '"timestamp": 1340821021000000, "hostname": "ubuntu", "text": '
        '"Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\\n '
        'closed for user root)", "pathspec": "{{\\"type_indicator\\": '
        '\\"TSK\\", \\"inode\\": 15, \\"location\\": \\"/var/log/syslog.1\\", '
        '\\"parent\\": \\"{{\\\\\\"type_indicator\\\\\\": \\\\\\"OS\\\\\\", '
        '\\\\\\"location\\\\\\": \\\\\\"/cases/image.dd\\\\\\"}}\\"}}", '
        '"inode": 12345678}}\n').format(self.event_object.uuid)

    self.formatter.EventBody(self.event_object)
    self.assertEquals(self.output.getvalue(), expected_string)


if __name__ == '__main__':
  unittest.main()
