#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Timesketch output class."""

import unittest

from mock import Mock
from mock import MagicMock

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


class TimesketchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the Timesketch output class."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._timesketch_output = timesketch_out.TimesketchOutputModule(
        output_mediator)


  def testMissingParameters(self):
    """Tests the GetMissingArguments function."""
    self.assertListEqual(
        self._timesketch_output.GetMissingArguments(), [u'timeline_name'])

    config = TimesketchTestConfig()

    self._timesketch_output.SetIndexName(config.index)
    self._timesketch_output.SetFlushInterval(config.flush_interval)
    self.assertListEqual(
        self._timesketch_output.GetMissingArguments(), [u'timeline_name'])

    self._timesketch_output.SetTimelineName(config.timeline_name)
    self.assertListEqual(self._timesketch_output.GetMissingArguments(), [])


if __name__ == '__main__':
  unittest.main()
