#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import mediator


class TestEvent(events.EventObject):
  DATA_TYPE = 'test:mediator'

  def __init__(self):
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.timestamp_desc = eventdata.EventTimestamp.CHANGE_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'


class TestEventFormatter(formatters_interface.EventFormatter):
  DATA_TYPE = 'test:mediator'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class OutputMediatorTest(unittest.TestCase):
  """Tests for the output mediator object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._output_mediator = mediator.OutputMediator(None)

  def testGetEventFormatter(self):
    """Tests the GetEventFormatter function."""
    event_object = TestEvent()

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    self.assertIsInstance(event_formatter, TestEventFormatter)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormattedMessages(self):
    """Tests the GetFormattedMessages function."""
    event_object = TestEvent()

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    expected_message = (
        u'Reporter <CRON> PID: 8442'
        u' (pam_unix(cron:session): session closed for user root)')

    message, message_short = self._output_mediator.GetFormattedMessages(
        event_object)
    self.assertEqual(message, expected_message)
    self.assertEqual(message_short, expected_message)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormattedSources(self):
    """Tests the GetFormattedSources function."""
    event_object = TestEvent()

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    self.assertEqual(source, u'Syslog')
    self.assertEqual(source_short, u'LOG')

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_object = TestEvent()

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    expected_attribute_names = set([u'text'])

    attribute_names = self._output_mediator.GetFormatStringAttributeNames(
        event_object)
    self.assertEqual(attribute_names, expected_attribute_names)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetHostname(self):
    """Tests the GetHostname function."""
    event_object = TestEvent()

    hostname = self._output_mediator.GetHostname(event_object)
    self.assertEqual(hostname, u'ubuntu')

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    event_object = TestEvent()

    macb_representation = self._output_mediator.GetMACBRepresentation(
        event_object)
    self.assertEqual(macb_representation, u'..C.')

  def testGetStoredHostname(self):
    """Tests the GetStoredHostname function."""
    stored_hostname = self._output_mediator.GetStoredHostname()
    self.assertIsNone(stored_hostname)

  def testGetUsername(self):
    """Tests the GetUsername function."""
    event_object = TestEvent()

    username = self._output_mediator.GetUsername(event_object)
    self.assertEqual(username, u'root')


if __name__ == '__main__':
  unittest.main()
