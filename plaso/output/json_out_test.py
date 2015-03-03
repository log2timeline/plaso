#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the JSON output class."""

import StringIO
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import event
from plaso.lib import timelib_test
from plaso.output import json_out
from plaso.output import test_lib


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


class JsonOutputTest(test_lib.LogOutputFormatterTestCase):
  """Tests for the JSON outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(JsonOutputTest, self).setUp()
    self.output = StringIO.StringIO()
    self.formatter = json_out.JsonOutputFormatter(
        None, self._formatter_mediator, filehandle=self.output)
    self.event_object = JsonTestEvent()

  def testWriteHeaderAndfooter(self):
    """Tests the WriteHeader and WriteFooter functions."""
    expected_header = u'{'
    expected_footer = u'{"event_foo": "{}"}'

    self.formatter.WriteHeader()

    header = self.output.getvalue()
    self.assertEqual(header, expected_header)

    self.formatter.WriteFooter()

    footer = self.output.getvalue()
    self.assertEqual(footer, expected_footer)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self.formatter.WriteEventBody(self.event_object)

    expected_event_body = (
        '"event_0": {{"username": "root", "display_name": "OS: '
        '/var/log/syslog.1", "uuid": "{0:s}", "data_type": "test:l2tjson", '
        '"timestamp": 1340821021000000, "hostname": "ubuntu", "text": '
        '"Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\\n '
        'closed for user root)", "pathspec": "{{\\"type_indicator\\": '
        '\\"TSK\\", \\"inode\\": 15, \\"location\\": \\"/var/log/syslog.1\\", '
        '\\"parent\\": \\"{{\\\\\\"type_indicator\\\\\\": \\\\\\"OS\\\\\\", '
        '\\\\\\"location\\\\\\": \\\\\\"/cases/image.dd\\\\\\"}}\\"}}", '
        '"inode": 12345678}},\n').format(self.event_object.uuid)

    event_body = self.output.getvalue()
    self.assertEqual(event_body, expected_event_body)


if __name__ == '__main__':
  unittest.main()
