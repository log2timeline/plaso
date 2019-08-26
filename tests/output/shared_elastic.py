#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared functionality for Elasticsearch output modules."""

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

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestElasticsearchOutputModule(
    shared_elastic.SharedElasticsearchOutputModule):
  """Elasticsearch output module for testing."""

  def _Connect(self):
    """Connects to an Elasticsearch server."""
    self._client = MagicMock()


@unittest.skipIf(shared_elastic.elasticsearch is None, 'missing elasticsearch')
class SharedElasticsearchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the shared functionality for Elasticsearch output modules."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'syslog:line',
       'display_name': 'log/syslog.1',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'some_additional_foo': True,
       'a_binary_field': b'binary',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString(
           '2012-06-27 18:17:01+00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testConnect(self):
    """Tests the _Connect function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertIsNone(output_module._client)

    output_module._Connect()

    self.assertIsNotNone(output_module._client)

  def testCreateIndexIfNotExists(self):
    """Tests the _CreateIndexIfNotExists function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

  def testFlushEvents(self):
    """Tests the _FlushEvents function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    output_module._InsertEvent(event, event_data, None)

    self.assertEqual(len(output_module._event_documents), 2)
    self.assertEqual(output_module._number_of_buffered_events, 1)

    output_module._FlushEvents()

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

  def testGetSanitizedEventValues(self):
    """Tests the _GetSanitizedEventValues function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    event_tag = events.EventTag()
    event_tag.AddLabel('Test')

    event_values = output_module._GetSanitizedEventValues(
        event, event_data, event_tag)

    expected_event_values = {
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
        'timestamp': 1340821021000000,
        'timestamp_desc': 'Content Modification Time',
    }

    self.assertIsInstance(event_values, dict)
    self.assertDictContainsSubset(expected_event_values, event_values)

  def testInsertEvent(self):
    """Tests the _InsertEvent function."""
    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

    output_module._InsertEvent(event, event_data, None)

    self.assertEqual(len(output_module._event_documents), 2)
    self.assertEqual(output_module._number_of_buffered_events, 1)

    output_module._InsertEvent(event, event_data, None)

    self.assertEqual(len(output_module._event_documents), 4)
    self.assertEqual(output_module._number_of_buffered_events, 2)

    output_module._FlushEvents()

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

  def testClose(self):
    """Tests the Close function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    output_module._Connect()

    self.assertIsNotNone(output_module._client)

    output_module.Close()

    self.assertIsNone(output_module._client)

  def testSetDocumentType(self):
    """Tests the SetDocumentType function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertEqual(
        output_module._document_type, output_module._DEFAULT_DOCUMENT_TYPE)

    output_module.SetDocumentType('test_document_type')

    self.assertEqual(output_module._document_type, 'test_document_type')

  def testSetFlushInterval(self):
    """Tests the SetFlushInterval function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertEqual(
        output_module._flush_interval, output_module._DEFAULT_FLUSH_INTERVAL)

    output_module.SetFlushInterval(1234)

    self.assertEqual(output_module._flush_interval, 1234)

  def testSetIndexName(self):
    """Tests the SetIndexName function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertIsNone(output_module._index_name)

    output_module.SetIndexName('test_index')

    self.assertEqual(output_module._index_name, 'test_index')

  def testSetPassword(self):
    """Tests the SetPassword function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertIsNone(output_module._password)

    output_module.SetPassword('test_password')

    self.assertEqual(output_module._password, 'test_password')

  def testSetServerInformation(self):
    """Tests the SetServerInformation function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertIsNone(output_module._host)
    self.assertIsNone(output_module._port)

    output_module.SetServerInformation('127.0.0.1', 1234)

    self.assertEqual(output_module._host, '127.0.0.1')
    self.assertEqual(output_module._port, 1234)

  def testSetUsername(self):
    """Tests the SetUsername function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    self.assertIsNone(output_module._username)

    output_module.SetUsername('test_username')

    self.assertEqual(output_module._username, 'test_username')

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestElasticsearchOutputModule(output_mediator)

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    output_module.WriteEventBody(event, event_data, None)

    self.assertEqual(len(output_module._event_documents), 2)
    self.assertEqual(output_module._number_of_buffered_events, 1)


if __name__ == '__main__':
  unittest.main()
