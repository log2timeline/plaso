#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Elasticsearch output module."""

import unittest

from mock import MagicMock

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import elastic

from tests.output import test_lib


if not elastic.Elasticsearch:
  elastic.Elasticsearch = MagicMock()


class ElasticTestEvent(events.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""
    super(ElasticTestEvent, self).__init__()
    self.display_name = u'log/syslog.1'
    self.filename = u'log/syslog.1'
    self.hostname = u'ubuntu'
    self.my_number = 123
    self.some_additional_foo = True
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN
    self.timestamp = event_timestamp


class ElasticSearchHelperTest(test_lib.OutputModuleTestCase):
  """Tests for the Elasticsearch helper class."""

  # pylint: disable=protected-access

  def testEventToDict(self):
    """Tests the _EventToDict function."""
    label = u'Test'
    event_tag = events.EventTag()
    event_tag.AddLabel(label)

    event_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    event = ElasticTestEvent(event_timestamp)
    event.tag = event_tag

    output_mediator = self._CreateOutputMediator()
    elasticsearch_helper = elastic.ElasticSearchHelper(
        output_mediator, u'127.0.0.1', 9200, 1000, u'test', {}, u'test_type')

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
        u'tag': [label],
        u'text': (u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                  u'session\n closed for user root)'),
        u'timestamp': event_timestamp,
        u'timestamp_desc': u'Content Modification Time',
    }
    event_dict = elasticsearch_helper._GetSanitizedEventValues(event)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)


if __name__ == '__main__':
  unittest.main()
