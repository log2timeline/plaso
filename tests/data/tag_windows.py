#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_windows.txt tagging file."""

import unittest

from plaso.containers import events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import filestat
from plaso.parsers import winevt
from plaso.parsers import winevtx
from plaso.parsers import winlnk
from plaso.parsers import winjob
from plaso.parsers import winprefetch
from plaso.parsers.bencode_plugins import utorrent
from plaso.parsers.esedb_plugins import srum
from plaso.parsers.olecf_plugins import summary
from plaso.parsers.sqlite_plugins import chrome_history
from plaso.parsers.sqlite_plugins import windows_timeline
from plaso.parsers.winreg_plugins import amcache
from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import bagmru
from plaso.parsers.winreg_plugins import lfu
from plaso.parsers.winreg_plugins import mrulist
from plaso.parsers.winreg_plugins import mrulistex
from plaso.parsers.winreg_plugins import officemru
from plaso.parsers.winreg_plugins import run
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
    # Test: data_type is 'fs:stat' AND
    #       filename contains PATH('Windows/Tasks/At')
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

    # Test: data_type is 'windows:evt:record'
    #       AND source_name is
    #       'Microsoft-Windows-Program-Compatibility-Assistant'
    #       AND event_identifier is 17
    attribute_values_per_name = {
        'event_identifier': [17],
        'source_name': ['Microsoft-Windows-Program-Compatibility-Assistant']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4673
    attribute_values_per_name = {
        'event_identifier': [4673],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
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
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4798
    attribute_values_per_name = {
        'event_identifier': [4798],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4799
    attribute_values_per_name = {
        'event_identifier': [4799],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Sysmon' AND
    #       event_identifier is 1
    attribute_values_per_name = {
        'event_identifier': [1],
        'source_name': ['Microsoft-Windows-Sysmon']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       event_identifier is 500
    attribute_values_per_name = {
        'event_identifier': [500],
        'source_name': ['Microsoft-Windows-Application-Experience']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Application-Experience' AND
    #       event_identifier is 505
    attribute_values_per_name = {
        'event_identifier': [505],
        'source_name': ['Microsoft-Windows-Application-Experience']}
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

    # Test: data_type is 'windows:srum:application_usage'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        srum.SRUMApplicationResourceUsageEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:registry:amcache'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        amcache.AMCacheFileEventData, attribute_values_per_name,
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

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP
    event_data.entries = 'Index: 0 [MRU Value a]: file.exe'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:mrulistex' AND
    #       entries contains '.exe'
    event_data = mrulistex.MRUListExEventData()
    event_data.entries = 'Index: 0 [MRU Value 1]: file.txt'

    # Set timestamp to 0 otherwise document_open rule triggers.
    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP
    event_data.entries = 'Index: 0 [MRU Value 1]: file.exe'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:userassist' AND
    #       value_name contains '.exe'
    attribute_values_per_name = {
        'value_name': ['file.exe']}
    self._CheckTaggingRule(
        userassist.UserAssistWindowsRegistryEventData,
        attribute_values_per_name, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Compatibility Assistant\\Store'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKCU\\Software\\Microsoft\\Windows NT\\' + \
                          'CurrentVersion\\AppCompatFlags\\' + \
                          'Compatibility Assistant\\Store'
    event_data.values = 'SIGN.MEDIA=XXX setup.exe: [REG_BINARY] (108 bytes)'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Explorer\\FeatureUsage\\AppSwitched'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKCU\\Software\\Microsoft\\CurrentVersion\\' + \
                          'Explorer\\FeatureUsage\\AppSwitched'
    event_data.values = '{00000000-0000-0000-0000-000000000000}\\' + \
                        'zzzzzzzz.exe: [REG_DWORD_LE] 1 ' + \
                        '{00000000-0000-0000-0000-000000000000}\\yyyy\\' + \
                        'xxxxxxxx.exe: [REG_DWORD_LE] 7'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Explorer\\FeatureUsage\\AppLauch'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKCU\\Software\\Microsoft\\CurrentVersion\\' + \
                          'Explorer\\FeatureUsage\\AppLauch'
    event_data.values = 'Chrome: [REG_DWORD_LE] 2'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Explorer\\FeatureUsage\\AppBadgeUpdated'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKCU\\Software\\Microsoft\\CurrentVersion\\' + \
                          'Explorer\\FeatureUsage\\AppBadgeUpdated'
    event_data.values = 'Chrome: [REG_DWORD_LE] 2'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Explorer\\FeatureUsage\\ShowJumpView'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKCU\\Software\\Microsoft\\CurrentVersion\\' + \
                          'Explorer\\FeatureUsage\\ShowJumpView'
    event_data.values = 'Microsoft.AutoGenerated.{00000000-0000-0000-' + \
                        '0000-000000000000}: [REG_DWORD_LE] 1 Microsoft' + \
                        '.Windows.RemoteDesktop: [REG_DWORD_LE] 1'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Search\\RecentApps\\'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows' + \
                          '\\CurrentVersion\\Search\\RecentApps\\' + \
                          '{00000000-0000-0000-0000-000000000000}'
    event_data.values = 'AppId: [REG_SZ] C:\\xxxx.exe LastAccessedTime: ' + \
                        '[REG_QWORD] 131581731096750000 LaunchCount:' + \
                        '[REG_DWORD_LE] 1'
    event_data.parser = 'winreg/winreg_default'

    storage_writer = self._TagEvent(event, event_data, None)

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains '\\Services\\bam\\UserSettings\\'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet' + \
                          '\\Services\\bam\\UserSettings\\S-1-5-18'
    event_data.values = 'SequenceNumber: [REG_DWORD_LE] 8 Version: ' + \
                        '[REG_DWORD_LE] 1 \\Device\\HarddiskVolume4\\' + \
                        'Program Files\\uvnc bvba\\UltraVNC\\winvnc.exe: ' + \
                        '[REG_BINARY] (24 bytes) \\Device\\HarddiskVolume4' + \
                        '\\Windows\\System32\\csrss.exe:' + \
                        ' [REG_BINARY] (24 bytes)'
    event_data.parser = 'winreg/winreg_default'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains 'WinClient\\SoftwareMonitoring\\MonitorLog\\'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\' + \
                          'LANDesk\\ManagementSuite\\WinClient\\' + \
                          'SoftwareMonitoring\\MonitorLog\\' + \
                          'C:/Program Files (x86)/Google/Temp/' + \
                          'GUMEFD7.tmp/GoogleUpdate.exe'
    event_data.values = 'Current Duration: [REG_BINARY] (8 bytes) ' + \
                        'Current User: [REG_SZ] Système First Started:' + \
                        ' [REG_BINARY] (8 bytes) Last Duration: ' + \
                        '[REG_BINARY] (8 bytes) Last Started: ' + \
                        '[REG_BINARY] (8 bytes) Total Duration: ' + \
                        '[REG_BINARY] (8 bytes) Total Runs: [REG_DWORD_LE] 1'
    event_data.parser = 'winreg/winreg_default'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:registry:key_value' AND
    #       key_path contains
    #       'Microsoft\\RADAR\\HeapLeakDetection\\DiagnosedApplications\\'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\' + \
                          'RADAR\\HeapLeakDetection\\DiagnosedApplications' + \
                          '\\java.exe'
    event_data.values = 'LastDetectionTime: [REG_QWORD] 131581732255493203'
    event_data.parser = 'winreg/winreg_default'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['application_execution'])

    # Test: data_type is 'windows:tasks:job'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        winjob.WinJobEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'windows:timeline:user_engaged'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        windows_timeline.WindowsTimelineUserEngagedEventData,
        attribute_values_per_name,
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
    #       entries not contains '.exe' AND timestamp > DATETIME(0)
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = mrulist.MRUListEventData()
    event_data.entries = 'Index: 0 [MRU Value a]: file.txt'

    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['document_open'])

    # Test: data_type is 'windows:registry:mrulistex' AND
    #       entries not contains '.exe' AND timestamp > DATETIME(0)
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = mrulistex.MRUListExEventData()
    event_data.entries = 'Index: 0 [MRU Value 1]: file.txt'

    event.timestamp = 0

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp = self._TEST_TIMESTAMP

    storage_writer = self._TagEvent(event, event_data, None)

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

  def testSessionDisconnection(self):
    """Tests the session_disconnection tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       event_identifier is 24
    attribute_values_per_name = {
        'event_identifier': [24],
        'source_name': [
            'Microsoft-Windows-TerminalServices-LocalSessionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['session_disconnection'])

  def testSessionReconnection(self):
    """Tests the session_reconnection tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 25 OR event_identifier is 1105)
    attribute_values_per_name = {
        'event_identifier': [25, 1105],
        'source_name': [
            'Microsoft-Windows-TerminalServices-LocalSessionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['session_reconnection'])

  def testShellStart(self):
    """Tests the shell_start tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND source_name is
    #       'Microsoft-Windows-TerminalServices-LocalSessionManager' AND
    #       (event_identifier is 22 OR event_identifier is 1102)
    attribute_values_per_name = {
        'event_identifier': [22, 1102],
        'source_name': [
            'Microsoft-Windows-TerminalServices-LocalSessionManager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['shell_start'])

  def testTaskSchedule(self):
    """Tests the task_schedule tagging rule."""
    # Test: data_type is 'windows:evt:record' AND
    #       source_name is 'Security' AND
    #       event_identifier is 602
    attribute_values_per_name = {
        'event_identifier': [602],
        'source_name': ['Security']}
    self._CheckTaggingRule(
        winevt.WinEvtRecordEventData, attribute_values_per_name,
        ['task_schedule'])

    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing' AND
    #       event_identifier is 4698
    attribute_values_per_name = {
        'event_identifier': [4698],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['task_schedule'])

  def testJobSuccess(self):
    """Tests the job_success tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-TaskScheduler' AND
    #       event_identifier is 102
    attribute_values_per_name = {
        'event_identifier': [102],
        'source_name': ['Microsoft-Windows-TaskScheduler']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['job_success'])

  def testActionSuccess(self):
    """Tests the action_success tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-TaskScheduler' AND
    #       event_identifier is 201
    attribute_values_per_name = {
        'event_identifier': [201],
        'source_name': ['Microsoft-Windows-TaskScheduler']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['action_success'])

  def testNameResolutionTimeout(self):
    """Tests the name_resolution_timeout tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-DNS-Client' AND
    #       event_identifier is 1014
    attribute_values_per_name = {
        'event_identifier': [1014],
        'source_name': ['Microsoft-Windows-DNS-Client']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['name_resolution_timeout'])

  def testTimeChange(self):
    """Tests the time_change tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Kernel-General' AND
    #       event_identifier is 1
    attribute_values_per_name = {
        'event_identifier': [1],
        'source_name': ['Microsoft-Windows-Kernel-General']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['time_change'])

  def testShutdown(self):
    """Tests the shutdown tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Kernel-General' AND
    #       event_identifier is 13
    attribute_values_per_name = {
        'event_identifier': [13],
        'source_name': ['Microsoft-Windows-Kernel-General']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['shutdown'])

  def testSystemStart(self):
    """Tests the system_start tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Kernel-General' AND
    #       event_identifier is 12
    attribute_values_per_name = {
        'event_identifier': [12],
        'source_name': ['Microsoft-Windows-Kernel-General']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['system_start'])

  def testSystemSleep(self):
    """Tests the system_sleep tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Kernel-Power' AND
    #       event_identifier is 12
    attribute_values_per_name = {
        'event_identifier': [42],
        'source_name': ['Microsoft-Windows-Kernel-Power']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['system_sleep'])

  def testSystemWake(self):
    """Tests the system_wake tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND (
    #       provider_identifier is '{cdc05e28-c449-49c6-b9d2-88cf761644df}' OR
    #       source_name is 'Microsoft-Windows-Power-Troubleshooter') AND
    #       event_identifier is 1
    attribute_values_per_name = {
        'event_identifier': [1],
        'provider_identifier': ['{cdc05e28-c449-49c6-b9d2-88cf761644df}']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['system_wake'])

    attribute_values_per_name = {
        'event_identifier': [1],
        'source_name': ['Microsoft-Windows-Power-Troubleshooter']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['system_wake'])

  def testAutorun(self):
    """Tests the autorun tagging rule."""
    # Test: data_type is 'windows:registry:boot_execute' AND
    #       (value contains '.exe' OR value contains '.dll')
    attribute_values_per_name = {
        'value': ['file.exe', 'file.dll']}
    self._CheckTaggingRule(
        lfu.WindowsBootExecuteEventData, attribute_values_per_name, ['autorun'])

    # Test: data_type is 'windows:registry:boot_verification' AND
    #       (image_path contains '.exe' OR image_path contains '.dll')
    attribute_values_per_name = {
        'image_path': ['file.exe', 'file.dll']}
    self._CheckTaggingRule(
        lfu.WindowsBootVerificationEventData, attribute_values_per_name,
        ['autorun'])

    # Test: data_type is 'windows:registry:run' AND
    #       (entries contains '.exe' OR entries contains '.dll')
    attribute_values_per_name = {
        'entries': ['file.exe', 'file.dll']}
    self._CheckTaggingRule(
        run.RunKeyEventData, attribute_values_per_name, ['autorun'])

  def testFileDownload(self):
    """Tests the file_download tagging rule."""
    # Test: data_type is 'chrome:history:file_downloaded'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        chrome_history.ChromeHistoryFileDownloadedEventData,
        attribute_values_per_name, ['file_download'])

    # Test: timestamp_desc is 'File Downloaded'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = utorrent.UTorrentEventData()

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = 'Downloaded Time'

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['file_download'])

  def testDocumentPrint(self):
    """Tests the document_print tagging rule."""
    # Test: data_type is 'olecf:summary_info' AND
    #       timestamp_desc is 'Last Printed Time'
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = summary.OLECFSummaryInformationEventData()

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event.timestamp_desc = definitions.TIME_DESCRIPTION_LAST_PRINTED

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['document_print'])

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

  def testRegistryModified(self):
    """Tests the registry_modified tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Security-Auditing'
    #       event_identifier is 4657
    attribute_values_per_name = {
        'event_identifier': [4657],
        'source_name': ['Microsoft-Windows-Security-Auditing']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['registry_modified'])

  def testServiceNew(self):
    """Tests the service_new tagging rule."""
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Service Control Manager' AND
    #       event_identifier is 7045
    attribute_values_per_name = {
        'event_identifier': [7045],
        'source_name': ['Service Control Manager']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['service_new'])

  def testEventLogCleared(self):
    """Tests the eventlog_cleared tagging rule."""
    # Test: data_type is 'windows:evt:record' AND
    #       source_name is 'Security' AND
    #       event_identifier is 517
    attribute_values_per_name = {
        'event_identifier': [517],
        'source_name': ['Security']}
    self._CheckTaggingRule(
        winevt.WinEvtRecordEventData, attribute_values_per_name,
        ['eventlog_cleared'])
    # Test: data_type is 'windows:evtx:record' AND
    #       source_name is 'Microsoft-Windows-Eventlog' AND
    #       (event_identifier is 104 OR event_identifier is 1102)
    attribute_values_per_name = {
        'event_identifier': [104, 1102],
        'source_name': ['Microsoft-Windows-Eventlog']}
    self._CheckTaggingRule(
        winevtx.WinEvtxRecordEventData, attribute_values_per_name,
        ['eventlog_cleared'])


if __name__ == '__main__':
  unittest.main()
