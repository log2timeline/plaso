#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Timesketch output module."""

from __future__ import unicode_literals

import unittest

try:
  from mock import MagicMock
except ImportError:
  from unittest.mock import MagicMock

from plaso.output import timesketch_out

from tests.output import test_lib


class TimesketchTestConfig(object):
  """Configuration for the tests."""
  timeline_name = 'Test'
  output_format = 'timesketch'
  index = ''
  show_stats = False
  flush_interval = 1000


class TestTimesketchOutputModule(timesketch_out.TimesketchOutputModule):
  """Timesketch output module for testing."""

  def _Connect(self):
    """Connects to an Elasticsearch server."""
    self._client = MagicMock()


@unittest.skipIf(timesketch_out.timesketch is None, 'missing timesketch')
class TimesketchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the Timesketch output module."""

  # pylint: disable=protected-access

  def testClose(self):
    """Tests the Close function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestTimesketchOutputModule(output_mediator)

    output_module._Connect()

    self.assertIsNotNone(output_module._client)

    output_module.Close()

    self.assertIsNone(output_module._client)

  def testMissingParameters(self):
    """Tests the GetMissingArguments function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestTimesketchOutputModule(output_mediator)

    missing_arguments = output_module.GetMissingArguments()
    self.assertEqual(missing_arguments, ['timeline_name'])

    config = TimesketchTestConfig()

    output_module.SetIndexName(config.index)
    output_module.SetFlushInterval(config.flush_interval)

    missing_arguments = output_module.GetMissingArguments()
    self.assertEqual(missing_arguments, ['timeline_name'])

    output_module.SetTimelineName(config.timeline_name)

    missing_arguments = output_module.GetMissingArguments()
    self.assertEqual(missing_arguments, [])

  def testSetTimelineName(self):
    """Tests the SetTimelineName function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestTimesketchOutputModule(output_mediator)

    self.assertIsNone(output_module._timeline_name)

    output_module.SetTimelineName('test')

    self.assertEqual(output_module._timeline_name, 'test')

  def testSetTimelineOwner(self):
    """Tests the SetTimelineOwner function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestTimesketchOutputModule(output_mediator)

    self.assertIsNone(output_module._timeline_owner)

    output_module.SetTimelineOwner('test_username')

    self.assertEqual(output_module._timeline_owner, 'test_username')

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestTimesketchOutputModule(output_mediator)

    self.assertIsNone(output_module._client)

    output_module.WriteHeader()

    self.assertIsNotNone(output_module._client)


if __name__ == '__main__':
  unittest.main()
