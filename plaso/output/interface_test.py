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
import os
import locale
import sys
import tempfile
import unittest

from plaso.output import interface


class DummyEvent(object):
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


class TestOutput(interface.LogOutputFormatter):
  """This is a test output module that provides a simple XML."""

  def __init__(self, filehandle):
    """Fake the store."""
    super(TestOutput, self).__init__(store=None, filehandle=filehandle)

  def StartEvent(self):
    self.filehandle.write(u'<Event>\n')

  def EventBody(self, event_object):
    self.filehandle.write((
        u'\t<Date>{0:s}</Date>\n\t<Time>{1:d}</Time>\n'
        u'\t<Entry>{2:s}</Entry>\n').format(
            event_object.date, event_object.timestamp, event_object.entry))

  def EndEvent(self):
    self.filehandle.write(u'</Event>\n')

  def FetchEntry(self, **_):
    pass

  def Start(self):
    self.filehandle.write(u'<EventFile>\n')

  def End(self):
    self.filehandle.write(u'</EventFile>\n')


class PlasoOutputUnitTest(unittest.TestCase):
  """The unit test for plaso output formatting."""

  def testOutput(self):
    """Test a test implementation of the output formatter."""
    events = [DummyEvent(123456, u'My Event Is Now!'),
              DummyEvent(123458, u'There is no tomorrow.'),
              DummyEvent(123462, u'Tomorrow is now.'),
              DummyEvent(123489, u'This is just some stuff to fill the line.')]

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
    self.assertEquals(lines[0], u'<EventFile>\n')
    self.assertEquals(lines[1], u'<Event>\n')
    self.assertEquals(lines[2], u'\t<Date>03/01/2012</Date>\n')
    self.assertEquals(lines[3], u'\t<Time>123456</Time>\n')
    self.assertEquals(lines[4], u'\t<Entry>My Event Is Now!</Entry>\n')
    self.assertEquals(lines[5], u'</Event>\n')
    self.assertEquals(lines[6], u'<Event>\n')
    self.assertEquals(lines[7], u'\t<Date>03/01/2012</Date>\n')
    self.assertEquals(lines[8], u'\t<Time>123458</Time>\n')
    self.assertEquals(lines[9], u'\t<Entry>There is no tomorrow.</Entry>\n')
    self.assertEquals(lines[10], u'</Event>\n')
    self.assertEquals(lines[11], u'<Event>\n')
    self.assertEquals(lines[-1], u'</EventFile>\n')

  def testOutputList(self):
    """Test listing up all available registered modules."""
    module_seen = False
    for name, description in interface.ListOutputFormatters():
      if 'TestOutput' in name:
        module_seen = True
        self.assertEquals(description, (
            u'This is a test output module that provides a simple XML.'))

    self.assertTrue(module_seen)


class EventBufferTest(unittest.TestCase):
  """Few unit tests for the EventBuffer class."""

  def testFlush(self):
    """Test to ensure we empty our buffers and sends to output properly."""
    with tempfile.NamedTemporaryFile() as fh:

      def CheckBufferLength(event_buffer, expected):
        if not event_buffer.check_dedups:
          expected = 0
        # pylint: disable=protected-access
        self.assertEquals(len(event_buffer._buffer_dict), expected)

      formatter = TestOutput(fh)
      event_buffer = interface.EventBuffer(formatter, False)

      event_buffer.Append(DummyEvent(123456, u'Now is now'))
      CheckBufferLength(event_buffer, 1)

      # Add three events.
      event_buffer.Append(DummyEvent(123456, u'OMG I AM DIFFERENT'))
      event_buffer.Append(DummyEvent(123456, u'Now is now'))
      event_buffer.Append(DummyEvent(123456, u'Now is now'))
      CheckBufferLength(event_buffer, 2)

      event_buffer.Flush()
      CheckBufferLength(event_buffer, 0)

      event_buffer.Append(DummyEvent(123456, u'Now is now'))
      event_buffer.Append(DummyEvent(123456, u'Now is now'))
      event_buffer.Append(DummyEvent(123456, u'Different again :)'))
      CheckBufferLength(event_buffer, 2)
      event_buffer.Append(DummyEvent(123457, u'Now is different'))
      CheckBufferLength(event_buffer, 1)


class OutputFilehandleTest(unittest.TestCase):
  """Few unit tests for the OutputFilehandle."""

  def setUp(self):
    self.preferred_encoding = locale.getpreferredencoding()

  def _GetLine(self):
    # Time, Þorri allra landsmanna hlýddu á atburðinn.
    return ('Time, \xc3\x9eorri allra landsmanna hl\xc3\xbdddu \xc3\xa1 '
            'atbur\xc3\xb0inn.\n').decode('utf-8')

  def testFilePath(self):
    temp_path = ''
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
      temp_path = temp_file.name

    with interface.OutputFilehandle(self.preferred_encoding) as fh:
      fh.Open(path=temp_path)
      fh.WriteLine(self._GetLine())

    line_read = u''
    with open(temp_path, 'rb') as output_file:
      line_read = output_file.read()

    os.remove(temp_path)
    self.assertEquals(line_read, self._GetLine().encode('utf-8'))

  def testStdOut(self):
    with interface.OutputFilehandle(self.preferred_encoding) as fh:
      fh.Open(sys.stdout)
      try:
        fh.WriteLine(self._GetLine())
        self.assertTrue(True)
      except (UnicodeEncodeError, UnicodeDecodeError):
        self.assertTrue(False)


if __name__ == '__main__':
  unittest.main()
