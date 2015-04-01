#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import locale
import sys
import tempfile
import unittest

from plaso.output import interface
from plaso.output import manager
from plaso.output import test_lib


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


class TestOutput(interface.OutputModule):
  """This is a test output module that provides a simple XML."""

  NAME = u'testoutput'
  DESCRIPTION = u'Test output that provides a simple mocked XML.'

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.
    """
    super(TestOutput, self).__init__(
        store, formatter_mediator, filehandle=filehandle, config=config,
        filter_use=filter_use)

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._file_object.write((
        u'\t<Date>{0:s}</Date>\n\t<Time>{1:d}</Time>\n'
        u'\t<Entry>{2:s}</Entry>\n').format(
            event_object.date, event_object.timestamp, event_object.entry))

  def WriteEventEnd(self):
    """Writes the end of an event object to the output."""
    self._file_object.write(u'</Event>\n')

  def WriteEventStart(self):
    """Writes the start of an event object to the output."""
    self._file_object.write(u'<Event>\n')

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._file_object.write(u'</EventFile>\n')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._file_object.write(u'<EventFile>\n')


manager.OutputManager.RegisterOutput(TestOutput)


class PlasoOutputUnitTest(test_lib.OutputModuleTestCase):
  """The unit test for plaso output formatting."""

  def testOutput(self):
    """Tests an implementation of output module."""
    events = [
        DummyEvent(123456, u'My Event Is Now!'),
        DummyEvent(123458, u'There is no tomorrow.'),
        DummyEvent(123462, u'Tomorrow is now.'),
        DummyEvent(123489, u'This is just some stuff to fill the line.')]

    lines = []
    with tempfile.NamedTemporaryFile() as fh:
      formatter = TestOutput(None, self._formatter_mediator, filehandle=fh)
      formatter.WriteHeader()
      for event_object in events:
        formatter.WriteEvent(event_object)
      formatter.WriteFooter()

      fh.seek(0)
      for line in fh:
        lines.append(line)

    self.assertEqual(len(lines), 22)
    self.assertEqual(lines[0], u'<EventFile>\n')
    self.assertEqual(lines[1], u'<Event>\n')
    self.assertEqual(lines[2], u'\t<Date>03/01/2012</Date>\n')
    self.assertEqual(lines[3], u'\t<Time>123456</Time>\n')
    self.assertEqual(lines[4], u'\t<Entry>My Event Is Now!</Entry>\n')
    self.assertEqual(lines[5], u'</Event>\n')
    self.assertEqual(lines[6], u'<Event>\n')
    self.assertEqual(lines[7], u'\t<Date>03/01/2012</Date>\n')
    self.assertEqual(lines[8], u'\t<Time>123458</Time>\n')
    self.assertEqual(lines[9], u'\t<Entry>There is no tomorrow.</Entry>\n')
    self.assertEqual(lines[10], u'</Event>\n')
    self.assertEqual(lines[11], u'<Event>\n')
    self.assertEqual(lines[-1], u'</EventFile>\n')

  def testOutputList(self):
    """Test listing up all available registered modules."""
    module_seen = False
    for name, description in manager.OutputManager.GetOutputs():
      if name == 'testoutput':
        module_seen = True
        self.assertEqual(description, (
            u'Test output that provides a simple mocked XML.'))

    self.assertTrue(module_seen)


class EventBufferTest(test_lib.OutputModuleTestCase):
  """Few unit tests for the EventBuffer class."""

  def testFlush(self):
    """Test to ensure we empty our buffers and sends to output properly."""
    with tempfile.NamedTemporaryFile() as fh:

      def CheckBufferLength(event_buffer, expected):
        if not event_buffer.check_dedups:
          expected = 0
        # pylint: disable=protected-access
        self.assertEqual(len(event_buffer._buffer_dict), expected)

      formatter = TestOutput(None, self._formatter_mediator, filehandle=fh)
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
    """Sets up the objects needed for this test."""
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
    self.assertEqual(line_read, self._GetLine().encode('utf-8'))

  def testStdOut(self):
    with interface.OutputFilehandle(self.preferred_encoding) as fh:
      fh.Open(sys.stdout)
      try:
        fh.WriteLine(self._GetLine())
      except (UnicodeDecodeError, UnicodeEncodeError):
        self.fail(u'Unicode decode/encode error exception.')


if __name__ == '__main__':
  unittest.main()
