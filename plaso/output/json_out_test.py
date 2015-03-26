#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the JSON output class."""

import io
import os
import sys
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import event
from plaso.lib import timelib
from plaso.output import json_out
from plaso.output import test_lib


class JsonTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2tjson'

  def __init__(self):
    """Initialize event with data."""
    super(JsonTestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.hostname = u'ubuntu'
    self.display_name = u'OS: /var/log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'

    os_location = u'{0:s}{1:s}'.format(
        os.path.sep, os.path.join(u'cases', u'image.dd'))
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=os_location)
    self.pathspec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/var/log/syslog.1',
        parent=os_path_spec)


class JsonOutputTest(test_lib.LogOutputFormatterTestCase):
  """Tests for the JSON outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(JsonOutputTest, self).setUp()
    self._output = io.BytesIO()
    self._formatter = json_out.JsonOutputFormatter(
        None, self._formatter_mediator, filehandle=self._output)
    self._event_object = JsonTestEvent()

  def testWriteHeaderAndfooter(self):
    """Tests the WriteHeader and WriteFooter functions."""
    expected_header = b'{'
    expected_footer = b'{"event_foo": "{}"}'

    self._formatter.WriteHeader()

    header = self._output.getvalue()
    self.assertEqual(header, expected_header)

    self._formatter.WriteFooter()

    footer = self._output.getvalue()
    self.assertEqual(footer, expected_footer)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self._formatter.WriteEventBody(self._event_object)

    expected_uuid = self._event_object.uuid.encode(u'utf-8')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01')

    if sys.platform.startswith('win'):
      expected_os_location = u'C:\\{0:s}'.format(
          os.path.join(u'cases', u'image.dd'))
      expected_os_location = expected_os_location.replace(u'\\', u'\\\\')
      expected_os_location = expected_os_location.replace(u'\\', u'\\\\')
      expected_os_location = expected_os_location.replace(u'\\', u'\\\\')
    else:
      expected_os_location = u'{0:s}{1:s}'.format(
          os.path.sep, os.path.join(u'cases', u'image.dd'))

    expected_os_location = expected_os_location.encode(u'utf-8')

    expected_event_body = (
        b'"event_0": {{"username": "root", "display_name": "OS: '
        b'/var/log/syslog.1", "uuid": "{0:s}", "data_type": "test:l2tjson", '
        b'"timestamp": {1:d}, "hostname": "ubuntu", "text": '
        b'"Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\\n '
        b'closed for user root)", "pathspec": {{"inode": 15, '
        b'"type_indicator": "TSK", "location": "/var/log/syslog.1", '
        b'"parent": {{"type_indicator": "OS", '
        b'"location": "{2:s}"}}}}, '
        b'"inode": 12345678}},\n').format(
            expected_uuid, expected_timestamp, expected_os_location)

    event_body = self._output.getvalue()
    self.assertEqual(event_body, expected_event_body)


if __name__ == '__main__':
  unittest.main()
