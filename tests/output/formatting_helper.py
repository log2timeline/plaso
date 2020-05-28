#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output module field formatting helper."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import formatting_helper

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:dynamic'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class FieldFormattingHelperTest(test_lib.OutputModuleTestCase):
  """Test the output module field formatting helper."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:dynamic',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

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

  def testFormatSourceShort(self):
    """Tests the _FormatSourceShort function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    try:
      source_short_string = test_helper._FormatSourceShort(
          event, event_data, event_data_stream)
    finally:
      formatters_manager.FormattersManager.DeregisterFormatter(
          TestEventFormatter)

    self.assertEqual(source_short_string, 'LOG')

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

  def testGetFormattedField(self):
    """Tests the GetFormattedField function."""
    output_mediator = self._CreateOutputMediator()
    test_helper = formatting_helper.FieldFormattingHelper(output_mediator)
    test_helper._FIELD_FORMAT_CALLBACKS = {'zone': '_FormatTimeZone'}

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    zone_string = test_helper.GetFormattedField(
        'zone', event, event_data, event_data_stream, None)
    self.assertEqual(zone_string, 'UTC')


if __name__ == '__main__':
  unittest.main()
