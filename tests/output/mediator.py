#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.engine import knowledge_base
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import mediator


class TestEvent(events.EventObject):
  """Test event object."""
  DATA_TYPE = 'test:mediator'

  def __init__(self):
    """Initializes an event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_CHANGE
    self.hostname = 'ubuntu'
    self.filename = 'log/syslog.1'
    self.text = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        'closed for user root)')
    self.username = 'root'


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:mediator'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class OutputMediatorTest(unittest.TestCase):
  """Tests for the output mediator object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._output_mediator = mediator.OutputMediator(
        knowledge_base_object, None)

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
        'Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)')

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
    self.assertEqual(source, 'Syslog')
    self.assertEqual(source_short, 'LOG')

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_object = TestEvent()

    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    expected_attribute_names = set(['text'])

    attribute_names = self._output_mediator.GetFormatStringAttributeNames(
        event_object)
    self.assertEqual(attribute_names, expected_attribute_names)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetHostname(self):
    """Tests the GetHostname function."""
    event_object = TestEvent()

    hostname = self._output_mediator.GetHostname(event_object)
    self.assertEqual(hostname, 'ubuntu')

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    event_object = TestEvent()

    macb_representation = self._output_mediator.GetMACBRepresentation(
        event_object)
    self.assertEqual(macb_representation, '..C.')

  def testGetStoredHostname(self):
    """Tests the GetStoredHostname function."""
    stored_hostname = self._output_mediator.GetStoredHostname()
    self.assertIsNone(stored_hostname)

  def testGetUsername(self):
    """Tests the GetUsername function."""
    event_object = TestEvent()

    username = self._output_mediator.GetUsername(event_object)
    self.assertEqual(username, 'root')


if __name__ == '__main__':
  unittest.main()
