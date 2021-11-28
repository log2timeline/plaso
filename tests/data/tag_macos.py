#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_macos.txt tagging file."""

import unittest

from plaso.containers import events
from plaso.containers import plist_event
from plaso.lib import definitions
from plaso.parsers import filestat
from plaso.parsers import syslog
from plaso.parsers.olecf_plugins import summary
from plaso.parsers.plist_plugins import ipod
from plaso.parsers.sqlite_plugins import appusage
from plaso.parsers.sqlite_plugins import chrome_history
from plaso.parsers.sqlite_plugins import ls_quarantine

from tests.data import test_lib


class MacOSTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_macos.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_macos.txt'

  def testRuleApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    # Test: data_type is 'macosx:application_usage'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        appusage.MacOSApplicationUsageEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'syslog:line' AND
    #       body contains 'COMMAND=/bin/launchctl'
    attribute_values_per_name = {
        'body': ['COMMAND=/bin/launchctl']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['application_execution'])

  def testRuleApplicationInstall(self):
    """Tests the application_install tagging rule."""
    # Test: data_type is 'plist:key' AND
    #       plugin is 'plist_install_history'
    attribute_values_per_name = {
        'plugin': ['plist_install_history']}
    self._CheckTaggingRule(
        plist_event.PlistTimeEventData, attribute_values_per_name,
        ['application_install'])

  def testRuleAutorun(self):
    """Tests the autorun tagging rule."""
    # Test: data_type is 'fs:stat' AND
    #       timestamp_desc is 'Creation Time' AND
    #       filename contains PATH('LaunchAgents') AND
    #       filename contains '.plist'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_CREATION

    event_data = filestat.FileStatEventData()
    event_data.filename = '/LaunchDaemons/test.plist'
    event_data.parser = 'filestat'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event_data = filestat.FileStatEventData()
    event_data.filename = '/LaunchAgents/test.plist'
    event_data.parser = 'filestat'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['autorun'])

  def testRuleFileDownload(self):
    """Tests the file_download tagging rule."""
    # Test: data_type is 'chrome:history:file_downloaded'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        chrome_history.ChromeHistoryFileDownloadedEventData,
        attribute_values_per_name, ['file_download'])

    # Test: data_type is 'macosx:lsquarantine'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        ls_quarantine.LsQuarantineEventData, attribute_values_per_name,
        ['file_download'])

    # Test: timestamp_desc is 'File Downloaded'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = filestat.FileStatEventData()
    event_data.parser = 'filestat'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['file_download'])

  def testRuleDeviceConnection(self):
    """Tests the device_connection tagging rule."""
    # Test: data_type is 'ipod:device:entry'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        ipod.IPodPlistEventData, attribute_values_per_name,
        ['device_connection'])

    # Test: data_type is 'plist:key' AND
    #       plugin is 'plist_airport'
    attribute_values_per_name = {
        'plugin': ['plist_airport']}
    self._CheckTaggingRule(
        plist_event.PlistTimeEventData, attribute_values_per_name,
        ['device_connection'])

  def testRuleDocumentPrint(self):
    """Tests the document_print tagging rule."""
    # Test: data_type is 'olecf:summary_info' AND
    #       timestamp_desc is 'Last Printed Time'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    summary_information = summary.OLECFSummaryInformation(None)
    event_data = summary_information.GetEventData()
    event_data.parser = 'olecf/olecf_summary'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = definitions.TIME_DESCRIPTION_LAST_PRINTED

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['document_print'])


if __name__ == '__main__':
  unittest.main()
