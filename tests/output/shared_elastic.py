#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the shared code for Elasticsearch based output modules."""

from __future__ import unicode_literals

import unittest

try:
  from mock import MagicMock
except ImportError:
  from unittest.mock import MagicMock

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import shared_elastic

from tests.output import test_lib


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


class SharedElasticsearchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for SharedElasticsearchOutputModule."""

  # pylint: disable=protected-access

  # TODO: improve test coverage
  # shared_elastic.Elasticsearch = MagicMock()

  def testGetSanitizedEventValues(self):
    """Tests the _GetSanitizedEventValues function."""
    event_tag = events.EventTag()
    event_tag.AddLabel('Test')

    event_timestamp = timelib.Timestamp.CopyFromString(
        '2012-06-27 18:17:01+00:00')
    event = ElasticTestEvent(event_timestamp)
    event.tag = event_tag

    output_mediator = self._CreateOutputMediator()
    output_module = shared_elastic.SharedElasticsearchOutputModule(
        output_mediator)

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
        'tag': ['Test'],
        'text': ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                 'session\n closed for user root)'),
        'timestamp': event_timestamp,
        'timestamp_desc': 'Content Modification Time',
    }

    event_values = output_module._GetSanitizedEventValues(event)
    self.assertIsInstance(event_values, dict)
    self.assertDictContainsSubset(expected_dict, event_values)


if __name__ == '__main__':
  unittest.main()
