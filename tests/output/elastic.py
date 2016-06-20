#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Elasticsearch output module."""

import unittest

from mock import MagicMock

from plaso.containers import events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import elastic

from tests.output import test_lib

elastic.Elasticsearch = MagicMock()


class ElasticTestEvent(events.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""
    super(ElasticTestEvent, self).__init__()
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


class ElasticSearchHelperTest(test_lib.OutputModuleTestCase):
  """Tests for the Elasticsearch helper class."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    plaso_timestamp = timelib.Timestamp()
    self._event_timestamp = plaso_timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    self._label = u'Test'
    self._event_object = ElasticTestEvent(self._event_timestamp)
    self._event_tag = events.EventTag()
    self._event_tag.uuid = self._event_object.uuid
    self._event_tag.AddLabel(self._label)
    self._event_object.tag = self._event_tag

    output_mediator = self._CreateOutputMediator()

    self._elasticsearch_helper = elastic.ElasticSearchHelper(
        output_mediator, u'127.0.0.1', 9200, 1000, u'test', {}, u'test_type')

  def testEventToDict(self):
    """Tests the _EventToDict function."""
    expected_dict = {
        u'data_type': u'syslog:line',
        u'datetime': u'2012-06-27T18:17:01+00:00',
        u'display_name': u'log/syslog.1',
        u'filename': u'log/syslog.1',
        u'hostname': u'ubuntu',
        u'message': u'[',
        u'my_number': 123,
        u'some_additional_foo': True,
        u'source_long': u'Log File',
        u'source_short': u'LOG',
        u'tag': [self._label],
        u'text': (u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                  u'session\n closed for user root)'),
        u'timestamp': self._event_timestamp,
        u'timestamp_desc': u'Content Modification Time',
    }
    # pylint: disable=protected-access
    event_dict = self._elasticsearch_helper._GetSanitizedEventValues(
        self._event_object)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)


if __name__ == '__main__':
  unittest.main()
