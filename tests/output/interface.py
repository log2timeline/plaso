#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output module interface."""

import io
import unittest

from plaso.lib import definitions
from plaso.output import formatting_helper
from plaso.output import interface
from plaso.output import manager

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestXMLEventFormattingHelper(formatting_helper.EventFormattingHelper):
  """XML output module event formatting helper for testing."""

  def __init__(self, output_mediator):
    """Initializes a dynamic selected delimiter separated values output module.

    Args:
      output_mediator (OutputMediator): an output mediator.
    """
    super(TestXMLEventFormattingHelper, self).__init__(output_mediator)
    self._field_formatting_helper = formatting_helper.FieldFormattingHelper()

  def GetFormattedEvent(self, event, event_data, event_data_stream, event_tag):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """
    # pylint: disable=protected-access
    date_time_string = self._field_formatting_helper._FormatDateTime(
        self._output_mediator, event, event_data, event_data_stream)

    return (
        '<Event>\n'
        '\t<DateTime>{0:s}</DateTime>\n'
        '\t<Entry>{1:s}</Entry>\n'
        '</Event>').format(date_time_string, event_data.entry)


class TestXMLOutputModule(interface.TextFileOutputModule):
  """XML output module for testing."""

  NAME = 'test_xml'
  DESCRIPTION = 'Test output that provides a simple mocked XML.'

  def WriteFooter(self):
    """Writes the footer to the output."""
    self.WriteLine('</EventFile>')

  def WriteHeader(self):
    """Writes the header to the output."""
    self.WriteLine('<EventFile>')


class TextFileOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the output module that writes to a text file."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'entry': 'My Event Is Now!',
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'There is no tomorrow.',
       'timestamp': '2012-06-27 18:18:23',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'Tomorrow is now.',
       'timestamp': '2012-06-27 19:11:54',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'entry': 'This is just some stuff to fill the line.',
       'timestamp': '2012-06-27 19:12:03',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testOutput(self):
    """Tests an implementation of output module."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    event_formatting_helper = TestXMLEventFormattingHelper(output_mediator)
    output_module = TestXMLOutputModule(
        output_mediator, event_formatting_helper)
    output_module._file_object = test_file_object

    output_module.WriteHeader()

    for event_values in self._TEST_EVENTS:
      event, event_data, event_data_stream = (
          containers_test_lib.CreateEventFromValues(event_values))
      output_module.WriteEvent(event, event_data, event_data_stream, None)

    output_module.WriteFooter()

    expected_output = (
        '<EventFile>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T18:17:01.000000+00:00</DateTime>\n'
        '\t<Entry>My Event Is Now!</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T18:18:23.000000+00:00</DateTime>\n'
        '\t<Entry>There is no tomorrow.</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T19:11:54.000000+00:00</DateTime>\n'
        '\t<Entry>Tomorrow is now.</Entry>\n'
        '</Event>\n'
        '<Event>\n'
        '\t<DateTime>2012-06-27T19:12:03.000000+00:00</DateTime>\n'
        '\t<Entry>This is just some stuff to fill the line.</Entry>\n'
        '</Event>\n'
        '</EventFile>\n')

    output = test_file_object.getvalue()
    self.assertEqual(output, expected_output)

  def testOutputList(self):
    """Test listing up all available registered modules."""
    manager.OutputManager.RegisterOutput(TestXMLOutputModule)

    test_output_class = None
    for name, output_class in manager.OutputManager.GetOutputClasses():
      if name == 'test_xml':
        test_output_class = output_class

    expected_description = 'Test output that provides a simple mocked XML.'
    self.assertIsNotNone(test_output_class)
    self.assertEqual(test_output_class.DESCRIPTION, expected_description)

    manager.OutputManager.DeregisterOutput(TestXMLOutputModule)


if __name__ == '__main__':
  unittest.main()
