#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Timesketch output class."""

import unittest

from mock import Mock
from mock import MagicMock

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import timesketch_out

from tests.output import test_lib


# Mock the imports if timesketch is not available. If timesketch is
# not available the timesketch attribute is set to None in the
# output module.
if timesketch_out.timesketch is None:
  timesketch_mock = Mock()
  timesketch_mock.create_app = MagicMock()

  # Mock out all imports.
  timesketch_out.timesketch = timesketch_mock
  timesketch_out.elastic_exceptions = Mock()
  timesketch_out.current_app = MagicMock()
  timesketch_out.ElasticSearchDataStore = Mock()
  timesketch_out.db_sessions = Mock()
  timesketch_out.SearchIndex = Mock()
  timesketch_out.User = Mock()


class TimesketchTestConfig(object):
  """Config object for the tests."""
  timeline_name = u'Test'
  output_format = u'timesketch'
  index = u''
  show_stats = False
  flush_interval = 1000


class TimesketchTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""
    super(TimesketchTestEvent, self).__init__()
    self.timestamp = event_timestamp
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')


class TimesketchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the Timesketch output class."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    plaso_timestamp = timelib.Timestamp()
    self._event_timestamp = plaso_timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    self._event_object = TimesketchTestEvent(self._event_timestamp)
    self._event_tag = event.EventTag()
    self._event_tag.uuid = self._event_object.uuid
    self._event_tag.tags = [u'Test tag']
    self._event_object.tag = self._event_tag

    output_mediator = self._CreateOutputMediator()
    self._timesketch_output = timesketch_out.TimesketchOutputModule(
        output_mediator)

  def testEventToDict(self):
    """Tests the _EventToDict function."""
    expected_dict = {
        u'my_number': 123,
        u'display_name': u'log/syslog.1',
        u'timestamp_desc': u'Content Modification Time',
        u'timestamp': self._event_timestamp,
        u'some_additional_foo': True,
        u'hostname': u'ubuntu',
        u'filename': u'log/syslog.1',
        u'data_type': u'syslog:line',
        u'source_long': u'Log File',
        u'source_short': u'LOG',
        u'tag': [u'Test tag'],
        u'text': (u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                 u'session\n closed for user root)'),
        u'message': u'[',
        u'datetime': u'2012-06-27T18:17:01+00:00'
    }
    # pylint: disable=protected-access
    event_dict = self._timesketch_output._GetSanitizedEventValues(
        self._event_object)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)

  def testMissingParameters(self):
    """Tests the GetMissingArguments function."""
    self.assertListEqual(
        self._timesketch_output.GetMissingArguments(), [u'timeline_name'])

    config = TimesketchTestConfig()

    self._timesketch_output.SetIndex(config.index)
    self._timesketch_output.SetFlushInterval(config.flush_interval)
    self.assertListEqual(
        self._timesketch_output.GetMissingArguments(), [u'timeline_name'])

    self._timesketch_output.SetName(config.timeline_name)
    self.assertListEqual(self._timesketch_output.GetMissingArguments(), [])


if __name__ == '__main__':
  unittest.main()
