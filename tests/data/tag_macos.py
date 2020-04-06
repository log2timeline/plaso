#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_macos.txt tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.containers import plist_event
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import filestat
from plaso.parsers import syslog
from plaso.parsers.olecf_plugins import summary
from plaso.parsers.plist_plugins import ipod
from plaso.parsers.sqlite_plugins import appusage
from plaso.parsers.sqlite_plugins import chrome
from plaso.parsers.sqlite_plugins import ls_quarantine

from tests.data import test_lib


class MacOSTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_macos.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_macos.txt'

  _TEST_TIMESTAMP = timelib.Timestamp.CopyFromString('2020-04-04 13:46:25')

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

  def testRuleDocumentPrint(self):
    """Tests the document_print tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    summary_information = summary.OLECFSummaryInformation(None)
    event_data = summary_information.GetEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = definitions.TIME_DESCRIPTION_LAST_PRINTED

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_print'])


if __name__ == '__main__':
  unittest.main()
