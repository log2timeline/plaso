#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output module interface."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import manager

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class LinearOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the linear output module."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'entry': 'My Event Is Now!',
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'There is no tomorrow.',
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:18:23'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'Tomorrow is now.',
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 19:11:54'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'This is just some stuff to fill the line.',
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 19:12:03'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testOutput(self):
    """Tests an implementation of output module."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = test_lib.TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    output_module.WriteHeader()

    for event_values in self._TEST_EVENTS:
      event, event_data = containers_test_lib.CreateEventFromValues(
          event_values)
      output_module.WriteEvent(event, event_data, None)

    output_module.WriteFooter()

    expected_output = (
        '<EventFile>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T18:17:01+00:00</DateTime>\n'
        '\t<Entry>My Event Is Now!</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T18:18:23+00:00</DateTime>\n'
        '\t<Entry>There is no tomorrow.</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T19:11:54+00:00</DateTime>\n'
        '\t<Entry>Tomorrow is now.</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T19:12:03+00:00</DateTime>\n'
        '\t<Entry>This is just some stuff to fill the line.</Entry>\n'
        '</Event>\n'
        '</EventFile>\n')

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testOutputList(self):
    """Test listing up all available registered modules."""
    manager.OutputManager.RegisterOutput(test_lib.TestOutputModule)

    test_output_class = None
    for name, output_class in manager.OutputManager.GetOutputClasses():
      if name == 'test_xml':
        test_output_class = output_class

    expected_description = 'Test output that provides a simple mocked XML.'
    self.assertIsNotNone(test_output_class)
    self.assertEqual(test_output_class.DESCRIPTION, expected_description)

    manager.OutputManager.DeregisterOutput(test_lib.TestOutputModule)


if __name__ == '__main__':
  unittest.main()
