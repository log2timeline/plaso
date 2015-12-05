#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from plaso.output import event_buffer

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


class EventBufferTest(test_lib.OutputModuleTestCase):
  """Few unit tests for the EventBuffer class."""

  def _CheckBufferLength(self, event_buffer_object, expected_length):
    """Checks the length of the event buffer.

    Args:
      event_buffer_object: the event buffer object (instance of EventBuffer).
      expect_length: the expected event buffer length.
    """
    if not event_buffer_object.check_dedups:
      expected_length = 0

    # pylint: disable=protected-access
    self.assertEqual(len(event_buffer_object._buffer_dict), expected_length)

  def testFlush(self):
    """Test to ensure we empty our buffers and sends to output properly."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = test_lib.TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    event_buffer_object = event_buffer.EventBuffer(output_module, False)

    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    self._CheckBufferLength(event_buffer_object, 1)

    # Add three events.
    event_buffer_object.Append(TestEvent(123456, u'OMG I AM DIFFERENT'))
    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    self._CheckBufferLength(event_buffer_object, 2)

    event_buffer_object.Flush()
    self._CheckBufferLength(event_buffer_object, 0)

    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    event_buffer_object.Append(TestEvent(123456, u'Different again :)'))
    self._CheckBufferLength(event_buffer_object, 2)
    event_buffer_object.Append(TestEvent(123457, u'Now is different'))
    self._CheckBufferLength(event_buffer_object, 1)


if __name__ == '__main__':
  unittest.main()
