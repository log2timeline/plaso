#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OpenSearch output module."""

import unittest

from unittest.mock import MagicMock

from dfvfs.path import fake_path_spec

from plaso.lib import definitions
from plaso.output import opensearch
from plaso.output import shared_opensearch

from tests.output import test_lib
from tests.containers import test_lib as containers_test_lib


class TestOpenSearchOutputModule(opensearch.OpenSearchOutputModule):
  """OpenSearch output module for testing."""

  def _Connect(self):
    """Connects to an OpenSearch server."""
    self._client = MagicMock()


class OpenSearchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the OpenSearch output module."""

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

  def testFlushEvents(self):
    """Tests the _FlushEvents function.

    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetDataFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = TestOpenSearchOutputModule()

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # TODO: add test for event_tag.
    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module._WriteFieldValues(output_mediator, field_values)

    self.assertEqual(len(output_module._event_documents), 2)
    self.assertEqual(output_module._number_of_buffered_events, 1)

    output_module._FlushEvents()

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function.

    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetDataFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = TestOpenSearchOutputModule()

    output_module._Connect()
    output_module._CreateIndexIfNotExists('test', {})

    self.assertEqual(len(output_module._event_documents), 0)
    self.assertEqual(output_module._number_of_buffered_events, 0)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # TODO: add test for event_tag.
    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module._WriteFieldValues(output_mediator, field_values)

    self.assertEqual(len(output_module._event_documents), 2)
    self.assertEqual(output_module._number_of_buffered_events, 1)

  def testWriteHeader(self):
    """Tests the WriteHeader function.

    Raises:
      SkipTest: if opensearch-py is missing.
    """
    if shared_opensearch.opensearchpy is None:
      raise unittest.SkipTest('missing opensearch-py')

    output_mediator = self._CreateOutputMediator()
    output_module = TestOpenSearchOutputModule()

    self.assertIsNone(output_module._client)

    output_module.WriteHeader(output_mediator)

    self.assertIsNotNone(output_module._client)


if __name__ == '__main__':
  unittest.main()
