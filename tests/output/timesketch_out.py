#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Timesketch output module."""

from __future__ import unicode_literals

import unittest

try:
  from mock import Mock
except ImportError:
  from unittest.mock import Mock

try:
  from mock import MagicMock
except ImportError:
  from unittest.mock import MagicMock

from plaso.output import timesketch_out

from tests.output import test_lib


# Mock the imports if timesketch is not available. If timesketch is
# not available the timesketch attribute is set to None in the
# output module.
if timesketch_out:
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
  """Configuration for the tests."""
  timeline_name = 'Test'
  output_format = 'timesketch'
  index = ''
  show_stats = False
  flush_interval = 1000


@unittest.skipIf(timesketch_out == None, 'missing timesketch')
class TimesketchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the Timesketch output module."""

  # TODO: test Close function

  def testMissingParameters(self):
    """Tests the GetMissingArguments function."""
    output_mediator = self._CreateOutputMediator()
    output_module = timesketch_out.TimesketchOutputModule(output_mediator)

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

  # TODO: test SetDocType function
  # TODO: test SetFlushInterval function
  # TODO: test SetIndexName function
  # TODO: test SetTimelineName function
  # TODO: test SetUserName function
  # TODO: test WriteEventBody function
  # TODO: test WriteHeader function


if __name__ == '__main__':
  unittest.main()
