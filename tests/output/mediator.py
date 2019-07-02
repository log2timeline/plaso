#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

from __future__ import unicode_literals

import unittest

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import mediator

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:mediator'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class OutputMediatorTest(test_lib.OutputModuleTestCase):
  """Tests for the output mediator object."""

  _TEST_EVENTS = [
      {'data_type': 'test:mediator',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE,
       'username': 'root'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name='myhost')
    knowledge_base_object.SetHostname(hostname_artifact)

    self._output_mediator = mediator.OutputMediator(knowledge_base_object, None)

  def testGetEventFormatter(self):
    """Tests the GetEventFormatter function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_formatter = self._output_mediator.GetEventFormatter(event_data)
    self.assertIsInstance(event_formatter, TestEventFormatter)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormattedMessages(self):
    """Tests the GetFormattedMessages function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    expected_message = (
        'Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)')

    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    message, message_short = self._output_mediator.GetFormattedMessages(
        event_data)
    self.assertEqual(message, expected_message)
    self.assertEqual(message_short, expected_message)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetFormattedSources(self):
    """Tests the GetFormattedSources function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    source_short, source = self._output_mediator.GetFormattedSources(
        event, event_data)
    self.assertEqual(source, 'Syslog')
    self.assertEqual(source_short, 'LOG')

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testGetHostname(self):
    """Tests the GetHostname function."""
    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    hostname = self._output_mediator.GetHostname(event_data)
    self.assertEqual(hostname, 'ubuntu')

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    macb_representation = self._output_mediator.GetMACBRepresentation(
        event, event_data)
    self.assertEqual(macb_representation, '..C.')

  def testGetStoredHostname(self):
    """Tests the GetStoredHostname function."""
    hostname = self._output_mediator.GetStoredHostname()
    self.assertEqual(hostname, 'myhost')

  def testGetUsername(self):
    """Tests the GetUsername function."""
    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username = self._output_mediator.GetUsername(event_data)
    self.assertEqual(username, 'root')


if __name__ == '__main__':
  unittest.main()
