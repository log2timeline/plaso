#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output module interface."""

import unittest

from plaso.output import manager

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class TestEvent(object):
  """Test event object."""

  def __init__(self, timestamp, entry):
    """Initializes an event object."""
    super(TestEvent, self).__init__()
    self.date = u'03/01/2012'
    try:
      self.timestamp = int(timestamp)
    except ValueError:
      self.timestamp = 0
    self.entry = entry


class LinearOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the linear output module."""

  def testOutput(self):
    """Tests an implementation of output module."""
    events = [
        TestEvent(123456, u'My Event Is Now!'),
        TestEvent(123458, u'There is no tomorrow.'),
        TestEvent(123462, u'Tomorrow is now.'),
        TestEvent(123489, u'This is just some stuff to fill the line.')]

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = test_lib.TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    output_module.WriteHeader()
    for event_object in events:
      output_module.WriteEvent(event_object)
    output_module.WriteFooter()

    expected_output = (
        b'<EventFile>\n'
        b'<Event>\n'
        b'\t<Date>03/01/2012</Date>\n'
        b'\t<Time>123456</Time>\n'
        b'\t<Entry>My Event Is Now!</Entry>\n'
        b'</Event>\n'
        b'<Event>\n'
        b'\t<Date>03/01/2012</Date>\n'
        b'\t<Time>123458</Time>\n'
        b'\t<Entry>There is no tomorrow.</Entry>\n'
        b'</Event>\n'
        b'<Event>\n'
        b'\t<Date>03/01/2012</Date>\n'
        b'\t<Time>123462</Time>\n'
        b'\t<Entry>Tomorrow is now.</Entry>\n'
        b'</Event>\n'
        b'<Event>\n'
        b'\t<Date>03/01/2012</Date>\n'
        b'\t<Time>123489</Time>\n'
        b'\t<Entry>This is just some stuff to fill the line.</Entry>\n'
        b'</Event>\n'
        b'</EventFile>\n')

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testOutputList(self):
    """Test listing up all available registered modules."""
    manager.OutputManager.RegisterOutput(test_lib.TestOutputModule)

    test_output_class = None
    for name, output_class in manager.OutputManager.GetOutputClasses():
      if name == u'test_xml':
        test_output_class = output_class

    expected_description = u'Test output that provides a simple mocked XML.'
    self.assertIsNotNone(test_output_class)
    self.assertEqual(test_output_class.DESCRIPTION, expected_description)

    manager.OutputManager.DeregisterOutput(test_lib.TestOutputModule)


if __name__ == '__main__':
  unittest.main()
