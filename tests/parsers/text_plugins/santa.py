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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 208)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Execution event with quarantine URL.
    expected_event_values = {
        'data_type': 'santa:execution',
        'date_time': '2018-08-19T03:17:55.765+00:00',
        'decision': 'ALLOW',
        'process_hash': (
            '78b43a13b5b608fe1a5a590f5f3ff112ff16ece7befc29fc84347125f6b9ca78'),
        'process_path': '/Applications/Skype.app/Contents/MacOS/Skype',
        'quarantine_url': (
            'https://endpoint920510.azureedge.net/s4l/s4l/download/mac/'
            'Skype-8.28.0.41.dmg')}

    self.CheckEventValues(storage_writer, events[46], expected_event_values)

    # File operation event log
    expected_event_values = {
        'action': 'WRITE',
        'data_type': 'santa:file_system_event',
        'date_time': '2018-08-19T04:02:47.911+00:00',
        'file_path': '/Users/qwerty/newfile',
        'gid': '20',
        'group': 'staff',
        'pid': '303',
        'ppid': '1',
        'process': 'Finder',
        'process_path': (
            '/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder'),
        'uid': '501',
        'user': 'qwerty'}

    self.CheckEventValues(storage_writer, events[159], expected_event_values)

    # Test a Disk mounts event.
    expected_event_values = {
        'action': 'DISKAPPEAR',
        'appearance': '2018-08-19T03:17:28.982Z',
        'bsd_name': 'disk2s1',
        'bus': 'Virtual Interface',
        'data_type': 'santa:diskmount',
        'date_time': '2018-08-19T03:17:29.036+00:00',
        'dmg_path': '/Users/qwerty/Downloads/Skype-8.28.0.41.dmg',
        'fs': 'hfs',
        'model': 'Apple Disk Image',
        'mount': None,
        'serial': None,
        'volume': 'Skype'}

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    # Test Disk event created from appearance timestamp.
    expected_event_values = {
        'data_type': 'santa:diskmount',
        'date_time': '2018-08-19T03:17:28.982+00:00',
        'timestamp_desc': 'First Connection Time'}

    self.CheckEventValues(storage_writer, events[35], expected_event_values)

  def testProcessWithCurrentFormat(self):
    """Tests the Process function with the current Santa log format."""
    plugin = santa.SantaTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['santa2.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # File rename operation event log
    expected_event_values = {
        'action': 'RENAME',
        'data_type': 'santa:file_system_event',
        'date_time': '2022-02-17T16:30:05.253+00:00',
        'file_new_path': '/private/var/db/santa/santa.log.6.gz',
        'file_path': '/private/var/db/santa/santa.log.5.gz',
        'gid': '0',
        'group': 'wheel',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'user': 'root'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Process exit log
    expected_event_values = {
        'action': 'EXIT',
        'data_type': 'santa:process_exit',
        'date_time': '2022-02-09T16:47:02.893+00:00',
        'gid': '1',
        'pid': '75780',
        'pid_version': '1765713',
        'ppid': '155',
        'uid': '0'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Link file operation event log
    expected_event_values = {
        'action': 'LINK',
        'data_type': 'santa:file_system_event',
        'date_time': '2022-02-17T16:30:05.257+00:00',
        'file_new_path': '/private/var/db/santa/santa.log.0',
        'file_path': '/private/var/db/santa/santa.log',
        'gid': '0',
        'group': 'wheel',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'user': 'root'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    # Execution event log
    expected_event_values = {
        'action': 'EXEC',
        'certificate_common_name': 'Software Signing',
        'certificate_hash':
            'd84db96af8c2e60ac4c851a21ec460f6f84e0235beb17d24a78712b9b021ed57',
        'data_type': 'santa:execution',
        'date_time': '2022-02-17T16:31:28.414+00:00',
        'decision': 'ALLOW',
        'long_reason': 'critical system binary',
        'process_hash':
            '25977d1584525b571fc6d19dcac1a768d0555c58777876869255de312dcfcaf3',
        'gid': '0',
        'group': 'wheel',
        'mode': 'M',
        'pid': '26364',
        'pid_version': '2228711',
        'ppid': '1',
        'process_arguments': (
            'xpcproxy com.apple.mdworker.shared.'
            '07000000-0000-0000-0000-000000000000'),
        'process_path': '/usr/libexec/xpcproxy',
        'reason': 'BINARY',
        'uid': '0',
        'user': 'root'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
