#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared functionality for OpenSearch output modules."""

import unittest

from unittest.mock import MagicMock

from dfvfs.path import fake_path_spec

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import shared_opensearch

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestOpenSearchOutputModule(
    shared_opensearch.SharedOpenSearchOutputModule):
  """OpenSearch output module for testing."""

  def _Connect(self):
    """Connects to an OpenSearch server."""
    self._client = MagicMock()

  # pylint: disable=unused-argument

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    return


class SharedOpenSearchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the shared functionality for OpenSearch output modules."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'a_binary_field': b'binary',
       'data_type': 'syslog:line',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'some_additional_foo': True,
       'path_spec': fake_path_spec.FakePathSpec(
           location='log/syslog.1'),
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01+00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testConnect(self):
    """Tests the _Connect function.

    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._client)

    output_module._Connect()

    self.assertIsNotNone(output_module._client)

  def testCreateIndexIfNotExists(self):
    """Tests the _CreateIndexIfNotExists function.
    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_module = TestOpenSearchOutputModule()

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

  def testClose(self):
    """Tests the Close function.

    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_module = TestOpenSearchOutputModule()

    output_module._Connect()

    self.assertIsNotNone(output_module._client)

    output_module.Close()

    self.assertIsNone(output_module._client)

  def testGetFieldValues(self):
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetDataFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = TestOpenSearchOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabel('Test')

    expected_field_values = {
        'a_binary_field': 'binary',
        'data_type': 'syslog:line',
        'datetime': '2012-06-27T18:17:01.000000+00:00',
        'display_name': 'FAKE:log/syslog.1',
        'filename': 'log/syslog.1',
        'hostname': 'ubuntu',
        'message': '[',
        'my_number': 123,
        'path_spec': (
            '{"__type__": "PathSpec", "location": "log/syslog.1", '
            '"type_indicator": "FAKE"}'),
        'some_additional_foo': True,
        'source_long': 'Log File',
        'source_short': 'LOG',
        'tag': ['Test'],
        'text': ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                 'session\n closed for user root)'),
        'timestamp': 1340821021000000,
        'timestamp_desc': 'Content Modification Time'}

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, expected_field_values)

  def testSetFlushInterval(self):
    """Tests the SetFlushInterval function."""
    output_module = TestOpenSearchOutputModule()

    self.assertEqual(
        output_module._flush_interval, output_module._DEFAULT_FLUSH_INTERVAL)

    output_module.SetFlushInterval(1234)

    self.assertEqual(output_module._flush_interval, 1234)

  def testSetIndexName(self):
    """Tests the SetIndexName function."""
    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._index_name)

    output_module.SetIndexName('test_index')

    self.assertEqual(output_module._index_name, 'test_index')

  def testSetPassword(self):
    """Tests the SetPassword function."""
    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._password)

    output_module.SetPassword('test_password')

    self.assertEqual(output_module._password, 'test_password')

  def testSetServerInformation(self):
    """Tests the SetServerInformation function."""
    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._host)
    self.assertIsNone(output_module._port)

    output_module.SetServerInformation('127.0.0.1', 1234)

    self.assertEqual(output_module._host, '127.0.0.1')
    self.assertEqual(output_module._port, 1234)

  def testSetUsername(self):
    """Tests the SetUsername function."""
    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._username)

    output_module.SetUsername('test_username')

    self.assertEqual(output_module._username, 'test_username')


if __name__ == '__main__':
  unittest.main()
