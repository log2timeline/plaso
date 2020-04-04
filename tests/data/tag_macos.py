#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_macos.txt tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.analysis import mediator as analysis_mediator
from plaso.analysis import tagging
from plaso.containers import events
from plaso.containers import plist_event
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import filestat
from plaso.parsers import syslog
from plaso.parsers.plist_plugins import ipod
from plaso.parsers.sqlite_plugins import appusage
from plaso.parsers.sqlite_plugins import chrome
from plaso.parsers.sqlite_plugins import ls_quarantine
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class MacOSTaggingFileTest(shared_test_lib.BaseTestCase):
  """Tests the tag_macos.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TEST_TIMESTAMP = timelib.Timestamp.CopyFromString('2020-04-04 13:46:25')

  def _CheckLabels(self, storage_writer, expected_labels):
    """Checks the labels of tagged events.

    Args:
      storage_writer (FakeStorageWriter): storage writer used for testing.
      expected_labels (list[str]): expected labels.
    """
    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)

    labels = set(labels)
    expected_labels = set(expected_labels)

    self.assertEqual(len(labels), len(expected_labels))
    self.assertEqual(sorted(labels), sorted(expected_labels))

  def _TagEvent(self, event, event_data):
    """Tags an event.

    Args:
      event (Event): event.
      event_data (EventData): event data.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the tag file does not exist.
    """
    tag_file_path = self._GetDataFilePath(['tag_macos.txt'])
    self._SkipIfPathNotExists(tag_file_path)

    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()
    storage_writer.AddEventData(event_data)
    storage_writer.AddEvent(event)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    mediator = analysis_mediator.AnalysisMediator(
        storage_writer, knowledge_base_object)

    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(tag_file_path)
    plugin.ExamineEvent(mediator, event, event_data)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAnalysisReport(analysis_report)

    return storage_writer

  def testRuleApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = appusage.MacOSApplicationUsageEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    event_data = syslog.SyslogLineEventData()
    event_data.body = 'some random log message'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data = syslog.SyslogLineEventData()
    event_data.body = 'somethin invoked COMMAND=/bin/launchctl'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

  def testRuleApplicationInstall(self):
    """Tests the application_install tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = plist_event.PlistTimeEventData()
    event_data.plugin = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data = plist_event.PlistTimeEventData()
    event_data.plugin = 'plist_install_history'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_install'])

  def testRuleAutorun(self):
    """Tests the autorun tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = 'HFS_DETECT crtime'

    event_data = filestat.FileStatEventData()
    event_data.filename = '/LaunchDaemons/test.plist'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data = filestat.FileStatEventData()
    event_data.filename = '/LaunchAgents/test.plist'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['autorun'])

  def testRuleFileDownload(self):
    """Tests the file_download tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = chrome.ChromeHistoryFileDownloadedEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['file_download'])

    event_data = ls_quarantine.LsQuarantineEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['file_download'])

    event_data = filestat.FileStatEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['file_download'])

  def testRuleDeviceConnection(self):
    """Tests the device_connection tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = ipod.IPodPlistEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['device_connection'])

    event_data = plist_event.PlistTimeEventData()
    event_data.plugin = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data = plist_event.PlistTimeEventData()
    event_data.plugin = 'plist_airport'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['device_connection'])

  # TODO: add tests for document_print tagging rule, this requires
  # changes in plaso.parsers.olecf_plugins.summary.


if __name__ == '__main__':
  unittest.main()
