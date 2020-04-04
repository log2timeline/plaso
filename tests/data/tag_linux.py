#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_linux.txt tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import bash_history
from plaso.parsers import docker
from plaso.parsers import selinux
from plaso.parsers import zsh_extended_history
from plaso.parsers.syslog_plugins import cron

from tests.data import test_lib


class LinuxTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_linux.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_linux.txt'

  _TEST_TIMESTAMP = timelib.Timestamp.CopyFromString('2020-04-04 14:56:39')

  def testRuleApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'bash:history:command'
    event_data = bash_history.BashHistoryEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'docker:json:layer'
    event_data = docker.DockerJSONLayerEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'selinux:line' AND audit_type is 'EXECVE'
    event_data = selinux.SELinuxLogEventData()
    event_data.audit_type = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.audit_type = 'EXECVE'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'shell:zsh:history'
    event_data = zsh_extended_history.ZshHistoryEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'syslog:cron:task_run'
    event_data = cron.CronTaskRunEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: reporter is 'sudo' AND body contains 'COMMAND='
    # TODO: implement

  # TODO: add tests for tagging rule: login
  # TODO: add tests for tagging rule: login_failed
  # TODO: add tests for tagging rule: logout
  # TODO: add tests for tagging rule: session_start
  # TODO: add tests for tagging rule: session_stop
  # TODO: add tests for tagging rule: boot
  # TODO: add tests for tagging rule: shutdown
  # TODO: add tests for tagging rule: runlevel
  # TODO: add tests for tagging rule: device_connection
  # TODO: add tests for tagging rule: device_disconnection
  # TODO: add tests for tagging rule: application_install
  # TODO: add tests for tagging rule: service_start
  # TODO: add tests for tagging rule: service_stop
  # TODO: add tests for tagging rule: promiscuous
  # TODO: add tests for tagging rule: crash


if __name__ == '__main__':
  unittest.main()
