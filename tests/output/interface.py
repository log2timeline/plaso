#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from plaso.output import interface
from plaso.output import manager

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class TestEvent(object):
  """Simple class that defines a dummy event."""

  def __init__(self, timestamp, entry):
    self.date = u'03/01/2012'
    try:
      self.timestamp = int(timestamp)
    except ValueError:
      self.timestamp = 0
    self.entry = entry
  def EqualityString(self):
    return u';'.join(map(str, [self.timestamp, self.entry]))


class TestOutputModule(interface.LinearOutputModule):
  """This is a test output module that provides a simple XML."""

  NAME = u'test_xml'
  DESCRIPTION = u'Test output that provides a simple mocked XML.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._WriteLine((
        u'\t<Date>{0:s}</Date>\n\t<Time>{1:d}</Time>\n'
        u'\t<Entry>{2:s}</Entry>\n').format(
            event_object.date, event_object.timestamp, event_object.entry))

  def WriteEventEnd(self):
    """Writes the end of an event object to the output."""
    self._WriteLine(u'</Event>\n')

  def WriteEventStart(self):
    """Writes the start of an event object to the output."""
    self._WriteLine(u'<Event>\n')

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._WriteLine(u'</EventFile>\n')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(u'<EventFile>\n')


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
    output_module = TestOutputModule(output_mediator)
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
    manager.OutputManager.RegisterOutput(TestOutputModule)

    test_output_class = None
    for name, output_class in manager.OutputManager.GetOutputClasses():
      if name == u'test_xml':
        test_output_class = output_class

    expected_description = u'Test output that provides a simple mocked XML.'
    self.assertIsNotNone(test_output_class)
    self.assertEqual(test_output_class.DESCRIPTION, expected_description)

    manager.OutputManager.DeregisterOutput(TestOutputModule)


class EventBufferTest(test_lib.OutputModuleTestCase):
  """Few unit tests for the EventBuffer class."""

  def _CheckBufferLength(self, event_buffer, expected_length):
    """Checks the length of the event buffer.

    Args:
      event_buffer: the event buffer object (instance of EventBuffer).
      expect_length: the expected event buffer length.
    """
    if not event_buffer.check_dedups:
      expected_length = 0

    # pylint: disable=protected-access
    self.assertEqual(len(event_buffer._buffer_dict), expected_length)

  def testFlush(self):
    """Test to ensure we empty our buffers and sends to output properly."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    event_buffer = interface.EventBuffer(output_module, False)

    event_buffer.Append(TestEvent(123456, u'Now is now'))
    self._CheckBufferLength(event_buffer, 1)

    # Add three events.
    event_buffer.Append(TestEvent(123456, u'OMG I AM DIFFERENT'))
    event_buffer.Append(TestEvent(123456, u'Now is now'))
    event_buffer.Append(TestEvent(123456, u'Now is now'))
    self._CheckBufferLength(event_buffer, 2)

    event_buffer.Flush()
    self._CheckBufferLength(event_buffer, 0)

    event_buffer.Append(TestEvent(123456, u'Now is now'))
    event_buffer.Append(TestEvent(123456, u'Now is now'))
    event_buffer.Append(TestEvent(123456, u'Different again :)'))
    self._CheckBufferLength(event_buffer, 2)
    event_buffer.Append(TestEvent(123457, u'Now is different'))
    self._CheckBufferLength(event_buffer, 1)


if __name__ == '__main__':
  unittest.main()
