#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_windows.txt tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import filestat
from plaso.parsers import winevt
from plaso.parsers import winevtx
from plaso.parsers import winlnk
from plaso.parsers import winjob
from plaso.parsers import winprefetch
from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import bagmru
from plaso.parsers.winreg_plugins import mrulist
from plaso.parsers.winreg_plugins import mrulistex
from plaso.parsers.winreg_plugins import officemru
from plaso.parsers.winreg_plugins import userassist

from tests.data import test_lib


class WindowsTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_windows.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_windows.txt'

  _TEST_TIMESTAMP = timelib.Timestamp.CopyFromString('2020-04-10 15:22:28')

  def testApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'fs:stat' AND filename contains 'Windows/Tasks/At'
    event_data = filestat.FileStatEventData()
    event_data.filename = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.filename = 'C:/Windows/Tasks/At/bogus.job'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 592
    event_data = winevt.WinEvtRecordEventData()
    event_data.event_identifier = 592
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Security'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 592

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4688
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 4688
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Security-Auditing'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 4688

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       strings contains 'user mode service' AND
    #       strings contains 'demand start'
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.strings = ['user mode service']

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.strings = ['user mode service', 'demand start']

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:lnk:link' AND
    #       filename contains 'Recent' AND (local_path contains '.exe' OR
    #       network_path contains '.exe' OR relative_path contains '.exe')
    event_data = winlnk.WinLnkLinkEventData()
    event_data.filename = 'bogus'
    event_data.local_path = 'file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.filename = 'Recent'
    event_data.local_path = 'file.txt'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.local_path = 'file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    event_data.local_path = None
    event_data.network_path = 'file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    event_data.network_path = None
    event_data.relative_path = 'file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:prefetch:execution'
    event_data = winprefetch.WinPrefetchExecutionEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:appcompatcache'
    event_data = appcompatcache.AppCompatCacheEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:mrulist' AND
    #       entries contains '.exe'
    event_data = mrulist.MRUListEventData()
    event_data.entries = 'Index: 0 [MRU Value a]: file.txt'

    # Set timestamp to 0 otherwise document_open rule triggers.
    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP
    event_data.entries = 'Index: 0 [MRU Value a]: file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:mrulistex' AND
    #       entries contains '.exe'
    event_data = mrulistex.MRUListExEventData()
    event_data.entries = 'Index: 0 [MRU Value 1]: file.txt'

    # Set timestamp to 0 otherwise document_open rule triggers.
    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP
    event_data.entries = 'Index: 0 [MRU Value 1]: file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:userassist' AND
    #       value_name contains '.exe'
    event_data = userassist.UserAssistWindowsRegistryEventData()
    event_data.value_name = 'file.txt'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.value_name = 'file.exe'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:tasks:job'
    event_data = winjob.WinJobEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_execution'])

  def testApplicationInstall(self):
    """Tests the application_install tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       (event_identifier is 903 OR event_identifier is 904)
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 903
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Application-Experience'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 903

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_install'])

    event_data.event_identifier = 904

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_install'])

  def testApplicationUpdate(self):
    """Tests the application_update tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       event_identifier is 905
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 905
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Application-Experience'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 905

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_update'])

  def testApplicationRemoval(self):
    """Tests the application_removal tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       (event_identifier is 907 OR event_identifier is 908)
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 907
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Application-Experience'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 907

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_removal'])

    event_data.event_identifier = 908

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['application_removal'])

  def testDocumentOpen(self):
    """Tests the document_open tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:registry:bagmru'
    event_data = bagmru.BagMRUEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_open'])

    # Test: data_type is 'windows:registry:mrulist' AND
    #       entries not contains '.exe' AND timestamp > 0
    event_data = mrulist.MRUListEventData()
    event_data.entries = 'Index: 0 [MRU Value a]: file.txt'

    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_open'])

    # Test: data_type is 'windows:registry:mrulistex' AND
    #       entries not contains '.exe' AND timestamp > 0
    event_data = mrulistex.MRUListExEventData()
    event_data.entries = 'Index: 0 [MRU Value 1]: file.txt'

    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_open'])

    # Test: data_type is 'windows:registry:office_mru'
    event_data = officemru.OfficeMRUWindowsRegistryEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_open'])

    # Test: data_type is 'windows:registry:office_mru_list'
    event_data = officemru.OfficeMRUListWindowsRegistryEventData()

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['document_open'])

  def testLoginFailed(self):
    """Tests the login_failed tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4625
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 4625
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Security-Auditing'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 4625

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_failed'])

  def testLoginAttempt(self):
    """Tests the login_attempt tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 540
    event_data = winevt.WinEvtRecordEventData()
    event_data.event_identifier = 540
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Security'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 540

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4624
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 4624
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Security-Auditing'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 4624

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 21 OR event_identifier is 1101)
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 21
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = (
        'Microsoft-Windows-TerminalServices-LocalSessionManager')

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 21

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    event_data.event_identifier = 1101

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-RemoteConnectionManager'
    #       AND (event_identifier is 1147 OR event_identifier is 1149)
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 1147
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = (
        'Microsoft-Windows-TerminalServices-RemoteConnectionManager')

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1147

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    event_data.event_identifier = 1149

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-User Profiles Service' AND
    #       event_identifier is 2
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 2
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-User Profiles Service'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 2

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Winlogon' AND
    #       event_identifier is 7001
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 7001
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Winlogon'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 7001

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['login_attempt'])

  def testLogoff(self):
    """Tests the logoff tagging rule."""
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 538
    event_data = winevt.WinEvtRecordEventData()
    event_data.event_identifier = 538
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Security'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 538

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4634
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 4634
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Security-Auditing'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 4634

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 23 OR event_identifier is 1103)
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 23
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = (
        'Microsoft-Windows-TerminalServices-LocalSessionManager')

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 23

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

    event_data.event_identifier = 1103

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-User Profiles Service' AND
    #       event_identifier is 4
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 4
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-User Profiles Service'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 4

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Winlogon' AND
    #       event_identifier is 7002
    event_data = winevtx.WinEvtxRecordEventData()
    event_data.event_identifier = 7002
    event_data.source_name = 'bogus'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 1
    event_data.source_name = 'Microsoft-Windows-Winlogon'

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 0)
    self._CheckLabels(storage_writer, [])

    event_data.event_identifier = 7002

    storage_writer = self._TagEvent(event, event_data)

    self.assertEqual(storage_writer.number_of_event_tags, 1)
    self._CheckLabels(storage_writer, ['logoff'])

  # TODO: add tests for session_disconnection tagging rule
  # TODO: add tests for session_reconnection tagging rule
  # TODO: add tests for shell_start tagging rule
  # TODO: add tests for task_schedule tagging rule
  # TODO: add tests for job_success tagging rule
  # TODO: add tests for action_success tagging rule
  # TODO: add tests for name_resolution_timeout tagging rule
  # TODO: add tests for time_change tagging rule
  # TODO: add tests for shutdown tagging rule
  # TODO: add tests for system_start tagging rule
  # TODO: add tests for system_sleep tagging rule
  # TODO: add tests for autorun tagging rule
  # TODO: add tests for file_download tagging rule
  # TODO: add tests for document_print tagging rule


if __name__ == '__main__':
  unittest.main()
