#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time MySQL output class."""

import unittest

from mock import Mock

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import mysql_4n6time

from tests.output import test_lib


# If MySQLdb is not available the MySQLdb attribute is set to None
# in the output module.
if mysql_4n6time.MySQLdb is None:
  mysql_4n6time.MySQLdb = Mock()


class MySQL4n6TimeTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""
    super(MySQL4n6TimeTestEvent, self).__init__()

    self.timestamp = event_timestamp
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root)')
    self.store_number = 1
    self.store_index = 1


class MySQL4n6TimeOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the 4n6time MySQL output class."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    plaso_timestamp = timelib.Timestamp()
    self._event_timestamp = plaso_timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    self._event_object = MySQL4n6TimeTestEvent(self._event_timestamp)
    output_mediator = self._CreateOutputMediator()
    self._output_module = mysql_4n6time.MySQL4n6TimeOutputModule(
        output_mediator)

  def testGetSanitizedEventValues(self):
    """Tests the _GetSanitizedEventValues function."""
    expected_dict = {
        u'type': u'Content Modification Time',
        u'host': u'ubuntu',
        u'filename': u'log/syslog.1',
        u'source': u'LOG',
        u'description': u'[',
        u'datetime': u'2012-06-27 18:17:01',
        u'inreport': u'',
        u'source_name': u'-',
        u'extra': (
            u'my_number: 123  some_additional_foo: True  text: '
            u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
            u'session closed for user root) '
        ),
        u'color': u'',
        u'tag': u'',
        u'timezone': u'UTC',
        u'inode': u'-',
        u'reportnotes': u'',
        u'sourcetype': u'Log File',
        u'event_identifier': u'-',
        u'store_number': 1,
        u'format': u'-',
        u'URL': u'-',
        u'store_index': 1,
        u'record_number': 0,
        u'MACB': u'M...',
        u'computer_name': u'-',
        u'offset': 0,
        u'evidence': u'-',
        u'user_sid': u'-',
        u'notes': u'-',
        u'vss_store_number': -1,
        u'user': u'-'
    }
    event_dict = self._output_module._GetSanitizedEventValues(
        self._event_object)
    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)


if __name__ == '__main__':
  unittest.main()
