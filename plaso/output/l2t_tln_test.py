#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the l2tTLN output class."""

import io
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import timelib
from plaso.output import l2t_tln
from plaso.output import test_lib


class TlnTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:tln'

  def __init__(self):
    """Initialize event with data."""
    super(TlnTestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
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


class L2TTlnTest(test_lib.LogOutputFormatterTestCase):
  """Tests for the TLN outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(L2TTlnTest, self).setUp()
    self._output = io.BytesIO()
    self._formatter = l2t_tln.L2tTlnOutputFormatter(
        None, self._formatter_mediator, filehandle=self._output)
    self._event_object = TlnTestEvent()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = b'Time|Source|Host|User|Description|TZ|Notes\n'

    self._formatter.WriteHeader()

    header = self._output.getvalue()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TlnTestEventFormatter)

    self._formatter.WriteEventBody(self._event_object)

    expected_event_body = (
        b'1340821021|LOG|ubuntu|root|Reporter <CRON> PID:  8442  '
        b'(pam_unix(cron:session): session closed for user root)|UTC'
        b'|File: OS: log/syslog.1 inode: 12345678\n')

    event_body = self._output.getvalue()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count(b'|'), 6)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TlnTestEventFormatter)


if __name__ == '__main__':
  unittest.main()
