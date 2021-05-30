#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output module field formatting helper."""

import unittest

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfvfs.path import fake_path_spec

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import formatting_helper

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
  """Field formatter helper for testing purposes."""

  _FIELD_FORMAT_CALLBACKS = {'zone': '_FormatTimeZone'}


class FieldFormattingHelperTest(test_lib.OutputModuleTestCase):
  """Test the output module field formatting helper."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'path_spec': fake_path_spec.FakePathSpec(
           location='log/syslog.1'),
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

  def testFormatDateTime(self):
    """Tests the _FormatDateTime function with dynamic time."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '2012-06-27T18:17:01.000000+00:00')

    output_mediator.SetTimezone('Europe/Amsterdam')

    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '2012-06-27T20:17:01.000000+02:00')

    output_mediator.SetTimezone('UTC')
    event.date_time = dfdatetime_semantic_time.InvalidTime()

    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, 'Invalid')

  def testFormatDateTimeWithoutDynamicTime(self):
    """Tests the _FormatDateTime function without dynamic time."""
    output_mediator = self._CreateOutputMediator(dynamic_time=False)
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # Test with event.date_time
    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '2012-06-27T18:17:01.000000+00:00')

    output_mediator.SetTimezone('Europe/Amsterdam')

    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '2012-06-27T20:17:01.000000+02:00')

    output_mediator.SetTimezone('UTC')
    event.date_time = dfdatetime_semantic_time.InvalidTime()

    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '0000-00-00T00:00:00.000000+00:00')

    # Test with event.timestamp
    event.date_time = None
    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '2012-06-27T18:17:01.000000+00:00')

    event.timestamp = 0
    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '0000-00-00T00:00:00.000000+00:00')

    event.timestamp = -9223372036854775808
    date_time_string = test_helper._FormatDateTime(
        event, event_data, event_data_stream)
    self.assertEqual(date_time_string, '0000-00-00T00:00:00.000000+00:00')

  def testFormatDisplayName(self):
    """Tests the _FormatDisplayName function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    display_name_string = test_helper._FormatDisplayName(
        event, event_data, event_data_stream)
    self.assertEqual(display_name_string, 'FAKE:log/syslog.1')

  def testFormatFilename(self):
    """Tests the _FormatFilename function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    filename_string = test_helper._FormatFilename(
        event, event_data, event_data_stream)
    self.assertEqual(filename_string, 'log/syslog.1')

  def testFormatHostname(self):
    """Tests the _FormatHostname function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    hostname_string = test_helper._FormatHostname(
        event, event_data, event_data_stream)
    self.assertEqual(hostname_string, 'ubuntu')

  def testFormatInode(self):
    """Tests the _FormatInode function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    inode_string = test_helper._FormatInode(
        event, event_data, event_data_stream)
    self.assertEqual(inode_string, '-')

  def testFormatMACB(self):
    """Tests the _FormatMACB function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    macb_string = test_helper._FormatMACB(event, event_data, event_data_stream)
    self.assertEqual(macb_string, '..C.')

  def testFormatMessage(self):
    """Tests the _FormatMessage function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    message_string = test_helper._FormatMessage(
        event, event_data, event_data_stream)

    expected_message_string = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
        'for user root)')
    self.assertEqual(message_string, expected_message_string)

  def testFormatMessageShort(self):
    """Tests the _FormatMessageShort function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    message_short_string = test_helper._FormatMessageShort(
        event, event_data, event_data_stream)

    expected_message_short_string = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
        'for user root)')
    self.assertEqual(message_short_string, expected_message_short_string)

  def testFormatSource(self):
    """Tests the _FormatSource function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    source_string = test_helper._FormatSource(
        event, event_data, event_data_stream)

    self.assertEqual(source_string, 'Test log file')

  def testFormatSourceShort(self):
    """Tests the _FormatSourceShort function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    source_short_string = test_helper._FormatSourceShort(
        event, event_data, event_data_stream)

    self.assertEqual(source_short_string, 'FILE')

  def testFormatTag(self):
    """Tests the _FormatTag function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    tag_string = test_helper._FormatTag(None)
    self.assertEqual(tag_string, '-')

    event_tag = events.EventTag()
    event_tag.AddLabel('one')
    event_tag.AddLabel('two')

    tag_string = test_helper._FormatTag(event_tag)
    self.assertEqual(tag_string, 'one two')

  def testFormatTime(self):
    """Tests the _FormatTime function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # Test with event.date_time
    time_string = test_helper._FormatTime(
        event, event_data, event_data_stream)
    self.assertEqual(time_string, '18:17:01')

    output_mediator.SetTimezone('Europe/Amsterdam')

    time_string = test_helper._FormatTime(
        event, event_data, event_data_stream)
    self.assertEqual(time_string, '20:17:01')

    output_mediator.SetTimezone('UTC')

    # Test with event.timestamp
    event.date_time = None
    time_string = test_helper._FormatTime(
        event, event_data, event_data_stream)
    self.assertEqual(time_string, '18:17:01')

    event.timestamp = 0
    time_string = test_helper._FormatTime(
        event, event_data, event_data_stream)
    self.assertEqual(time_string, '--:--:--')

    event.timestamp = -9223372036854775808
    time_string = test_helper._FormatTime(
        event, event_data, event_data_stream)
    self.assertEqual(time_string, '--:--:--')

  def testFormatTimeZone(self):
    """Tests the _FormatTimeZone function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    zone_string = test_helper._FormatTimeZone(
        event, event_data, event_data_stream)
    self.assertEqual(zone_string, 'UTC')

  def testFormatUsername(self):
    """Tests the _FormatUsername function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    username_string = test_helper._FormatUsername(
        event, event_data, event_data_stream)
    self.assertEqual(username_string, '-')

  # TODO: add coverage for _ReportEventError

  def testGetFormattedField(self):
    """Tests the GetFormattedField function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = TestFieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    zone_string = test_helper.GetFormattedField(
        'zone', event, event_data, event_data_stream, None)
    self.assertEqual(zone_string, 'UTC')


if __name__ == '__main__':
  unittest.main()
