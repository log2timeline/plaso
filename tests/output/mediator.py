#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

from __future__ import unicode_literals

import unittest

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.output import mediator

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class OutputMediatorTest(test_lib.OutputModuleTestCase):
  """Tests for the output mediator object."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE,
       'username': 'root'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name='myhost')
    knowledge_base_object.SetHostname(hostname_artifact)

    self._output_mediator = mediator.OutputMediator(knowledge_base_object, None)

  # TODO: add tests for GetDisplayNameForPathSpec

  def testGetHostname(self):
    """Tests the GetHostname function."""
    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    hostname = self._output_mediator.GetHostname(event_data)
    self.assertEqual(hostname, 'ubuntu')

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    macb_representation = self._output_mediator.GetMACBRepresentation(
        event, event_data)
    self.assertEqual(macb_representation, '..C.')

  # TODO: add tests for GetRelativePathForPathSpec

  def testGetStoredHostname(self):
    """Tests the GetStoredHostname function."""
    hostname = self._output_mediator.GetStoredHostname()
    self.assertEqual(hostname, 'myhost')

  def testGetUsername(self):
    """Tests the GetUsername function."""
    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username = self._output_mediator.GetUsername(event_data)
    self.assertEqual(username, 'root')


if __name__ == '__main__':
  unittest.main()
