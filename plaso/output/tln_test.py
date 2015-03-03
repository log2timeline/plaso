#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the TLN output class."""

import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.output import test_lib
from plaso.output import tln


class TlnTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2ttln'

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


class L2TTlnTestEventFormatter(formatters_interface.EventFormatter):
  """Formatter for the test event."""
  DATA_TYPE = 'test:l2ttln'
  FORMAT_STRING = u'{text}'
  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


formatters_manager.FormattersManager.RegisterFormatter(L2TTlnTestEventFormatter)


class TlnTest(test_lib.LogOutputFormatterTestCase):
  """Tests for the TLN outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(TlnTest, self).setUp()
    self.output = StringIO.StringIO()
    self.formatter = tln.TlnOutputFormatter(
        None, self._formatter_mediator, filehandle=self.output)
    self.event_object = TlnTestEvent()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = u'Time|Source|Host|User|Description\n'

    self.formatter.WriteHeader()

    header = self.output.getvalue()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self.formatter.WriteEventBody(self.event_object)

    expected_event_body = (
        u'1340821021|LOG|ubuntu|root|Reporter <CRON> PID:  8442  '
        u'(pam_unix(cron:session): session closed for user root)\n')

    event_body = self.output.getvalue()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count(u'|'), 4)


if __name__ == '__main__':
  unittest.main()
