#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_windows.txt tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.lib import definitions
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

  def testApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    # Test: data_type is 'fs:stat' AND filename contains 'Windows/Tasks/At'
    attribute_values_per_name = {
        'filename': ['C:/Windows/Tasks/At/bogus.job']}
    self._CheckTaggingRule(
        filestat.FileStatEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 592
    attribute_values_per_name = {
        'event_identifier': [592],
        'source_name': ['Security']}
    self._CheckTaggingRule(
        winevt.WinEvtRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4688
    attribute_values_per_name = {
        'event_identifier': [4688],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       strings contains 'user mode service' AND
    #       strings contains 'demand start'
    attribute_values_per_name = {
        'strings': [['user mode service', 'demand start']]}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:lnk:link' AND
    #       filename contains 'Recent' AND (local_path contains '.exe' OR
    #       network_path contains '.exe' OR relative_path contains '.exe')
    attribute_values_per_name = {
        'filename': ['Recent'],
        'local_path': ['file.exe']}
    self._CheckTaggingRule(
        winlnk.WinLnkLinkEventData, attribute_values_per_name,
        ['application_execution'])

    attribute_values_per_name = {
        'filename': ['Recent'],
        'network_path': ['file.exe']}
    self._CheckTaggingRule(
        winlnk.WinLnkLinkEventData, attribute_values_per_name,
        ['application_execution'])

    attribute_values_per_name = {
        'filename': ['Recent'],
        'relative_path': ['file.exe']}
    self._CheckTaggingRule(
        winlnk.WinLnkLinkEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:prefetch:execution'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        winprefetch.WinPrefetchExecutionEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:registry:appcompatcache'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        appcompatcache.AppCompatCacheEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:registry:mrulist' AND
    #       entries contains '.exe'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

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
    attribute_values_per_name = {
        'value_name': ['file.exe']}
    self._CheckTaggingRule(
        userassist.UserAssistWindowsRegistryEventData,
        attribute_values_per_name, ['application_execution'])

    # Test: data_type is 'windows:tasks:job'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        winjob.WinJobEventData, attribute_values_per_name,
        ['application_execution'])

  def testApplicationInstall(self):
    """Tests the application_install tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       (event_identifier is 903 OR event_identifier is 904)
    attribute_values_per_name = {
        'event_identifier': [903, 904],
        'source_name': ['Microsoft-Windows-Application-Experience']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_install'])

  def testApplicationUpdate(self):
    """Tests the application_update tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       event_identifier is 905
    attribute_values_per_name = {
        'event_identifier': [905],
        'source_name': ['Microsoft-Windows-Application-Experience']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_update'])

  def testApplicationRemoval(self):
    """Tests the application_removal tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       (event_identifier is 907 OR event_identifier is 908)
    attribute_values_per_name = {
        'event_identifier': [907, 908],
        'source_name': ['Microsoft-Windows-Application-Experience']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_removal'])

  def testDocumentOpen(self):
    """Tests the document_open tagging rule."""
    # Test: data_type is 'windows:registry:bagmru'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        bagmru.BagMRUEventData, attribute_values_per_name, ['document_open'])

    # Test: data_type is 'windows:registry:mrulist' AND
    #       entries not contains '.exe' AND timestamp > 0
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

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
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

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
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        officemru.OfficeMRUWindowsRegistryEventData, attribute_values_per_name,
        ['document_open'])

    # Test: data_type is 'windows:registry:office_mru_list'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        officemru.OfficeMRUListWindowsRegistryEventData,
        attribute_values_per_name, ['document_open'])

  def testLoginFailed(self):
    """Tests the login_failed tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4625
    attribute_values_per_name = {
        'event_identifier': [4625],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_failed'])

  def testLoginAttempt(self):
    """Tests the login_attempt tagging rule."""
    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 540
    attribute_values_per_name = {
        'event_identifier': [540],
        'source_name': ['Security']}
    self._CheckTaggingRule(
        winevt.WinEvtRecordEventData, attribute_values_per_name,
        ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4624
    attribute_values_per_name = {
        'event_identifier': [4624],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 21 OR event_identifier is 1101)
    attribute_values_per_name = {
        'event_identifier': [21, 1101],
        'source_name': [
            'Microsoft-Windows-TerminalServices-LocalSessionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-RemoteConnectionManager'
    #       AND (event_identifier is 1147 OR event_identifier is 1149)
    attribute_values_per_name = {
        'event_identifier': [1147, 1149],
        'source_name': [
            'Microsoft-Windows-TerminalServices-RemoteConnectionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-User Profiles Service' AND
    #       event_identifier is 2
    attribute_values_per_name = {
        'event_identifier': [2],
        'source_name': ['Microsoft-Windows-User Profiles Service']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_attempt'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Winlogon' AND
    #       event_identifier is 7001
    attribute_values_per_name = {
        'event_identifier': [7001],
        'source_name': ['Microsoft-Windows-Winlogon']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['login_attempt'])

  def testLogoff(self):
    """Tests the logoff tagging rule."""
    # Test: data_type is 'windows:evt:record' AND source_name is 'Security' AND
    #       event_identifier is 538
    attribute_values_per_name = {
        'event_identifier': [538],
        'source_name': ['Security']}
    self._CheckTaggingRule(
        winevt.WinEvtRecordEventData, attribute_values_per_name, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4634
    attribute_values_per_name = {
        'event_identifier': [4634],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 23 OR event_identifier is 1103)
    attribute_values_per_name = {
        'event_identifier': [23, 1103],
        'source_name': [
            'Microsoft-Windows-TerminalServices-LocalSessionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-User Profiles Service' AND
    #       event_identifier is 4
    attribute_values_per_name = {
        'event_identifier': [4],
        'source_name': ['Microsoft-Windows-User Profiles Service']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name, ['logoff'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Winlogon' AND
    #       event_identifier is 7002
    attribute_values_per_name = {
        'event_identifier': [7002],
        'source_name': ['Microsoft-Windows-Winlogon']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name, ['logoff'])

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

  def testFirewallChange(self):
    """Tests the firewall_change tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Windows Firewall With Advanced
    #           Security' AND
    #       (event_identifier is 2003 OR event_identifier is 2004 OR
    #        event_identifier is 2005 OR event_identifier is 2006)
    attribute_values_per_name = {
        'event_identifier': [2003, 2004, 2005, 2006],
        'source_name': [
            'Microsoft-Windows-Windows Firewall With Advanced Security']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['firewall_change'])


if __name__ == '__main__':
  unittest.main()
