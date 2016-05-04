#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event buffer."""

import unittest

from plaso.output import event_buffer

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

  def EqualityString(self):
    """Returns a string describing the event object in terms of object equality.

    Returns:
      A string representation of the event object that can be used for equality
      comparison.
    """
    return u';'.join(map(str, [self.timestamp, self.entry]))


class EventBufferTest(test_lib.OutputModuleTestCase):
  """Tests the event buffer."""

  # pylint: disable=protected-access

  def _CheckBufferLength(self, event_buffer_object, expected_length):
    """Checks the length of the event buffer.

    Args:
      event_buffer_object: the event buffer object (instance of EventBuffer).
      expect_length: the expected event buffer length.
    """
    if not event_buffer_object.check_dedups:
      expected_length = 0

    self.assertEqual(len(event_buffer_object._events_per_key), expected_length)

  def testFlush(self):
    """Tests the Flush function."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = test_lib.TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    event_buffer_object = event_buffer.EventBuffer(output_module, False)

    event_buffer_object.Append(TestEvent(123456, u'Now is now'))
    self._CheckBufferLength(event_buffer_object, 1)

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
