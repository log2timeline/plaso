#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains tests for the output formatter."""

import tempfile
import unittest

from plaso.lib import output


class DummyEvent(object):
  """Simple class that defines a dummy event."""

  def __init__(self, timestamp, entry):
    self.date = '03/01/2012'
    try:
      self.timestamp = int(timestamp)
    except ValueError:
      self.timestamp = 0
    self.entry = entry
  def EqualityString(self):
    return ';'.join(map(str, [self.timestamp, self.entry]))


class TestOutput(output.LogOutputFormatter):
  """This is a dummy test module that provides a simple XML."""

  def __init__(self, filehandle):
    """Fake the store."""
    super(TestOutput, self).__init__(store=None, filehandle=filehandle)

  def StartEvent(self):
    self.filehandle.write('<Event>\n')

  def EventBody(self, event_object):
    self.filehandle.write(
        '\t<Date>%s</Date>\n\t<Time>%d</Time>\n\t<Entry>%s</Entry>\n' % (
            event_object.date,
            event_object.timestamp,
            event_object.entry))

  def EndEvent(self):
    self.filehandle.write('</Event>\n')

  def FetchEntry(self, **_):
    pass

  def Start(self):
    self.filehandle.write('<EventFile>\n')

  def End(self):
    self.filehandle.write('</EventFile>\n')


class PlasoOutputUnitTest(unittest.TestCase):
  """The unit test for plaso output formatting."""

  def testOutput(self):
    """Test a dummy implementation of the output formatter."""
    events = [DummyEvent(123456, 'My Event Is Now!'),
              DummyEvent(123458, 'There is no tomorrow.'),
              DummyEvent(123462, 'Tomorrow is now.'),
              DummyEvent(123489, 'This is just some stuff to fill the line.')]

    lines = []
    with tempfile.NamedTemporaryFile() as fh:
      formatter = TestOutput(fh)
      formatter.Start()
      for event_object in events:
        formatter.WriteEvent(event_object)
      formatter.End()

      fh.seek(0)
      for line in fh:
        lines.append(line)

    self.assertEquals(len(lines), 22)
    self.assertEquals(lines[0], '<EventFile>\n')
    self.assertEquals(lines[1], '<Event>\n')
    self.assertEquals(lines[2], '\t<Date>03/01/2012</Date>\n')
    self.assertEquals(lines[3], '\t<Time>123456</Time>\n')
    self.assertEquals(lines[4], '\t<Entry>My Event Is Now!</Entry>\n')
    self.assertEquals(lines[5], '</Event>\n')
    self.assertEquals(lines[6], '<Event>\n')
    self.assertEquals(lines[7], '\t<Date>03/01/2012</Date>\n')
    self.assertEquals(lines[8], '\t<Time>123458</Time>\n')
    self.assertEquals(lines[9], '\t<Entry>There is no tomorrow.</Entry>\n')
    self.assertEquals(lines[10], '</Event>\n')
    self.assertEquals(lines[11], '<Event>\n')
    self.assertEquals(lines[-1], '</EventFile>\n')

  def testOutputList(self):
    """Test listing up all available registed modules."""
    module_seen = False
    for name, description in output.ListOutputFormatters():
      if 'TestOutput' in name:
        module_seen = True
        self.assertEquals(description, (
            'This is a dummy test module that '
            'provides a simple XML.'))

    self.assertTrue(module_seen)


class EventBufferTest(unittest.TestCase):
  """Few unit tests for the EventBuffer class."""

  def testFlush(self):
    """Test to ensure we empty our buffers and sends to output properly."""
    with tempfile.NamedTemporaryFile() as fh:

      def CheckBufferLength(event_buffer, expected):
        if not event_buffer.check_dedups:
          expected = 0
        # pylint: disable-msg=W0212
        self.assertEquals(len(event_buffer._buffer_dict), expected)

      formatter = TestOutput(fh)
      event_buffer = output.EventBuffer(formatter, False)

      event_buffer.Append(DummyEvent(123456, 'Now is now'))
      CheckBufferLength(event_buffer, 1)

      # Add three events.
      event_buffer.Append(DummyEvent(123456, 'OMG I AM DIFFERENT'))
      event_buffer.Append(DummyEvent(123456, 'Now is now'))
      event_buffer.Append(DummyEvent(123456, 'Now is now'))
      CheckBufferLength(event_buffer, 2)

      event_buffer.Flush()
      CheckBufferLength(event_buffer, 0)

      event_buffer.Append(DummyEvent(123456, 'Now is now'))
      event_buffer.Append(DummyEvent(123456, 'Now is now'))
      event_buffer.Append(DummyEvent(123456, 'Different again :)'))
      CheckBufferLength(event_buffer, 2)
      event_buffer.Append(DummyEvent(123457, 'Now is different'))
      CheckBufferLength(event_buffer, 1)


if __name__ == '__main__':
  unittest.main()
