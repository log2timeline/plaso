#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a unit test for the output formatter of plaso."""
import tempfile
import unittest

from plaso.lib import output


class DummyEvent(object):
  """Simple class that defines a dummy event."""

  def __init__(self, timestamp, entry):
    self.date = '03/01/2012'
    try:
      self.time = int(timestamp)
    except ValueError:
      self.time = 0
    self.entry = entry


class TestOutput(output.LogOutputFormatter):
  """A very simple implementation of the output formatter."""

  def StartEvent(self):
    self.filehandle.write('<Event>\n')

  def EventBody(self, event):
    self.filehandle.write(
        '\t<Date>%s</Date>\n\t<Time>%d</Time>\n\t<Entry>%s</Entry>\n' % (
            event.date,
            event.time,
            event.entry))

  def EndEvent(self):
    self.filehandle.write('</Event>\n')

  def Start(self):
    self.filehandle.write('<EventFile>\n')

  def End(self):
    self.filehandle.write('</EventFile>\n')

  def Usage(self):
    return 'This is a dummy test module that provides a simple XML.'


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
      for event in events:
        formatter.WriteEvent(event)
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
    for name, description in output.ListOutputFormatters():
      self.assertEquals(name, 'TestOutput')
      self.assertEquals(description, ('This is a dummy test module that '
                                      'provides a simple XML.'))


if __name__ == '__main__':
  unittest.main()
