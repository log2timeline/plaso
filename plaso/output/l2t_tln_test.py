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
"""Tests for the l2tTLN output class."""

import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.output import l2t_tln


class TlnTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:tln'

  def __init__(self):
    """Initialize event with data."""
    super(TlnTestEvent, self).__init__()
    self.timestamp = 1340821021000000
    self.hostname = u'ubuntu'
    self.display_name = u'OS: log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'


class TlnTestEventFormatter(formatters_interface.EventFormatter):
  """Formatter for the test event."""
  DATA_TYPE = 'test:tln'
  FORMAT_STRING = u'{text}'
  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


formatters_manager.FormattersManager.RegisterFormatter(TlnTestEventFormatter)


class L2TTlnTest(unittest.TestCase):
  """Tests for the TLN outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    self.output = StringIO.StringIO()
    self.formatter = l2t_tln.L2ttln(None, self.output)
    self.event_object = TlnTestEvent()

  def testStart(self):
    """Test ensures header line is outputted as expected."""
    correct_line = u'Time|Source|Host|User|Description|TZ|Notes\n'

    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), correct_line)

  def testEventBody(self):
    """Test ensures that returned lines returned are formatted as TLN."""

    self.formatter.EventBody(self.event_object)
    correct = (u'1340821021|LOG|ubuntu|root|Reporter <CRON> PID:  8442  '
               u'(pam_unix(cron:session): session closed for user root)|UTC'
               u'|File: OS: log/syslog.1 inode: 12345678\n')
    self.assertEquals(self.output.getvalue(), correct)

  def testEventBodyNoStrayPipes(self):
    """Test ensures that the only pipes are the six field delimiters."""

    self.formatter.EventBody(self.event_object)
    self.assertEquals(self.output.getvalue().count(u'|'), 6)


if __name__ == '__main__':
  unittest.main()
