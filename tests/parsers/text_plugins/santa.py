#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Santa log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import santa

from tests.parsers.text_plugins import test_lib


class SantaTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Santa log text parser plugin."""

  def testProcessWithLegacyFormat(self):
    """Tests the Process function with the legacy Santa log format."""
    plugin = santa.SantaTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['santa.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 191)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Execution event with quarantine URL.
    expected_event_values = {
        'data_type': 'santa:execution',
        'decision': 'ALLOW',
        'last_run_time': '2018-08-19T03:17:55.765+00:00',
        'process_hash': (
            '78b43a13b5b608fe1a5a590f5f3ff112ff16ece7befc29fc84347125f6b9ca78'),
        'process_path': '/Applications/Skype.app/Contents/MacOS/Skype',
        'quarantine_url': (
            'https://endpoint920510.azureedge.net/s4l/s4l/download/mac/'
            'Skype-8.28.0.41.dmg')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 35)
    self.CheckEventData(event_data, expected_event_values)

    # File operation event log
    expected_event_values = {
        'action': 'WRITE',
        'data_type': 'santa:file_system_event',
        'file_path': '/Users/qwerty/newfile',
        'gid': '20',
        'group': 'staff',
        'last_written_time': '2018-08-19T04:02:47.911+00:00',
        'pid': '303',
        'ppid': '1',
        'process': 'Finder',
        'process_path': (
            '/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder'),
        'uid': '501',
        'user': 'qwerty'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 142)
    self.CheckEventData(event_data, expected_event_values)

    # Test a Disk mounts event.
    expected_event_values = {
        'action': 'DISKAPPEAR',
        'appearance_time': '2018-08-19T03:17:28.982+00:00',
        'bsd_name': 'disk2s1',
        'bus': 'Virtual Interface',
        'data_type': 'santa:diskmount',
        'dmg_path': '/Users/qwerty/Downloads/Skype-8.28.0.41.dmg',
        'fs': 'hfs',
        'last_written_time': '2018-08-19T03:17:29.036+00:00',
        'model': 'Apple Disk Image',
        'mount': None,
        'serial': None,
        'volume': 'Skype'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 27)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithCurrentFormat(self):
    """Tests the Process function with the current Santa log format."""
    plugin = santa.SantaTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['santa2.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # File rename operation event log
    expected_event_values = {
        'action': 'RENAME',
        'data_type': 'santa:file_system_event',
        'file_new_path': '/private/var/db/santa/santa.log.6.gz',
        'file_path': '/private/var/db/santa/santa.log.5.gz',
        'gid': '0',
        'group': 'wheel',
        'last_written_time': '2022-02-17T16:30:05.253+00:00',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'user': 'root'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Process exit log
    expected_event_values = {
        'action': 'EXIT',
        'data_type': 'santa:process_exit',
        'exit_time': '2022-02-09T16:47:02.893+00:00',
        'gid': '1',
        'pid': '75780',
        'pid_version': '1765713',
        'ppid': '155',
        'uid': '0'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Link file operation event log
    expected_event_values = {
        'action': 'LINK',
        'data_type': 'santa:file_system_event',
        'file_new_path': '/private/var/db/santa/santa.log.0',
        'file_path': '/private/var/db/santa/santa.log',
        'gid': '0',
        'group': 'wheel',
        'last_written_time': '2022-02-17T16:30:05.257+00:00',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'user': 'root'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Execution event log
    expected_event_values = {
        'action': 'EXEC',
        'certificate_common_name': 'Software Signing',
        'certificate_hash':
            'd84db96af8c2e60ac4c851a21ec460f6f84e0235beb17d24a78712b9b021ed57',
        'data_type': 'santa:execution',
        'decision': 'ALLOW',
        'gid': '0',
        'group': 'wheel',
        'last_run_time': '2022-02-17T16:31:28.414+00:00',
        'long_reason': 'critical system binary',
        'mode': 'M',
        'pid': '26364',
        'pid_version': '2228711',
        'ppid': '1',
        'process_arguments': (
            'xpcproxy com.apple.mdworker.shared.'
            '07000000-0000-0000-0000-000000000000'),
        'process_hash':
            '25977d1584525b571fc6d19dcac1a768d0555c58777876869255de312dcfcaf3',
        'process_path': '/usr/libexec/xpcproxy',
        'reason': 'BINARY',
        'uid': '0',
        'user': 'root'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
