#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event buffer."""

import unittest

from plaso.containers import events
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

  def testGetEventIdentifier(self):
    """Tests the _GetEventIdentifier function."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = test_lib.TestOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    event_buffer_object = event_buffer.EventBuffer(output_module, False)

    event_a = events.EventObject()
    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = u'mock:nothing'
    event_a.inode = 124
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False
    event_a_identifier = event_buffer_object._GetEventIdentifier(event_a)

    event_b = events.EventObject()
    event_b.timestamp = 123
    event_b.timestamp_desc = u'LAST WRITTEN'
    event_b.data_type = u'mock:nothing'
    event_b.inode = 124
    event_b.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False
    event_b_identifier = event_buffer_object._GetEventIdentifier(event_b)

    event_c = events.EventObject()
    event_c.timestamp = 123
    event_c.timestamp_desc = u'LAST UPDATED'
    event_c.data_type = u'mock:nothing'
    event_c.inode = 124
    event_c.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False
    event_c_identifier = event_buffer_object._GetEventIdentifier(event_c)

    event_d = events.EventObject()
    event_d.timestamp = 14523
    event_d.timestamp_desc = u'LAST WRITTEN'
    event_d.data_type = u'mock:nothing'
    event_d.inode = 124
    event_d.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False
    event_d_identifier = event_buffer_object._GetEventIdentifier(event_d)

    event_e = events.EventObject()
    event_e.timestamp = 123
    event_e.timestamp_desc = u'LAST WRITTEN'
    event_e.data_type = u'mock:nothing'
    event_e.inode = 623423
    event_e.filename = u'c:/afrit/öñṅûŗ₅ḱŖūα.txt'
    event_e.another_attribute = False
    event_e_identifier = event_buffer_object._GetEventIdentifier(event_e)

    event_f = events.EventObject()
    event_f.timestamp = 14523
    event_f.timestamp_desc = u'LAST WRITTEN'
    event_f.data_type = u'mock:nothing'
    event_f.inode = 124
    event_f.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_f.another_attribute = False
    event_f.weirdness = u'I am a potato'
    event_f_identifier = event_buffer_object._GetEventIdentifier(event_f)

    self.assertEqual(event_a_identifier, event_b_identifier)
    self.assertNotEqual(event_a_identifier, event_c_identifier)
    self.assertEqual(event_a_identifier, event_e_identifier)
    self.assertNotEqual(event_c_identifier, event_d_identifier)
    self.assertNotEqual(event_d_identifier, event_f_identifier)

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
