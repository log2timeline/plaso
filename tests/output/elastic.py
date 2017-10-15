#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Elasticsearch output module."""

from __future__ import unicode_literals

import unittest

try:
  from mock import MagicMock
except ImportError:
  from unittest.mock import MagicMock

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import elastic

from tests.output import test_lib


if not elastic.Elasticsearch:
  elastic.Elasticsearch = MagicMock()


class ElasticTestEvent(events.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""
    super(ElasticTestEvent, self).__init__()
    self.display_name = 'log/syslog.1'
    self.filename = 'log/syslog.1'
    self.hostname = 'ubuntu'
    self.my_number = 123
    self.some_additional_foo = True
    self.text = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        'closed for user root)')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN
    self.timestamp = event_timestamp


class ElasticSearchHelperTest(test_lib.OutputModuleTestCase):
  """Tests for the Elasticsearch helper class."""

  # pylint: disable=protected-access

  def testEventToDict(self):
    """Tests the _EventToDict function."""
    label = 'Test'
    event_tag = events.EventTag()
    event_tag.AddLabel(label)

    event_timestamp = timelib.Timestamp.CopyFromString(
        '2012-06-27 18:17:01+00:00')
    event = ElasticTestEvent(event_timestamp)
    event.tag = event_tag

    output_mediator = self._CreateOutputMediator()
    elasticsearch_helper = elastic.ElasticSearchHelper(
        output_mediator, '127.0.0.1', 9200, 1000, 'test', {}, 'test_type')

    expected_dict = {
        'data_type': 'syslog:line',
        'datetime': '2012-06-27T18:17:01+00:00',
        'display_name': 'log/syslog.1',
        'filename': 'log/syslog.1',
        'hostname': 'ubuntu',
        'message': '[',
        'my_number': 123,
        'some_additional_foo': True,
        'source_long': 'Log File',
        'source_short': 'LOG',
        'tag': [label],
        'text': ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                 'session\n closed for user root)'),
        'timestamp': event_timestamp,
        'timestamp_desc': 'Content Modification Time',
    }
    event_dict = elasticsearch_helper._GetSanitizedEventValues(event)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)


if __name__ == '__main__':
  unittest.main()
