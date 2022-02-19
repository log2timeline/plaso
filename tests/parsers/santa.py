#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Santa log parser."""

import unittest

from plaso.parsers import santa

from tests.parsers import test_lib


class SantaUnitTest(test_lib.ParserTestCase):
  """Tests for Santa log parser."""

  def testParseLegacyFormat(self):
    """Tests the Parse function on the legacy Santa log format."""
    parser = santa.SantaParser()
    storage_writer = self._ParseFile(['santa.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 208)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Execution event with quarantine URL.
    expected_event_values = {
        'date_time': '2018-08-19 03:17:55.765',
        'data_type': 'santa:execution',
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
        'date_time': '2018-08-19 04:02:47.911',
        'data_type': 'santa:file_system_event',
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
        'date_time': '2018-08-19 03:17:29.036',
        'data_type': 'santa:diskmount',
        'dmg_path': '/Users/qwerty/Downloads/Skype-8.28.0.41.dmg',
        'fs': 'hfs',
        'model': 'Apple Disk Image',
        'mount': '',
        'serial': '',
        'volume': 'Skype'}

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    # Test Disk event created from appearance timestamp.
    expected_event_values = {
        'date_time': '2018-08-19 03:17:28.982',
        'data_type': 'santa:diskmount',
        'timestamp_desc': 'First Connection Time'}

    self.CheckEventValues(storage_writer, events[35], expected_event_values)

  def testParseCurrentFormat(self):
    """Tests Parse function on the current Santa log format."""
    parser = santa.SantaParser()
    storage_writer = self._ParseFile(['santa2.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # File rename operation event log
    expected_event_values = {
        'action': 'RENAME',
        'date_time': '2022-02-17 16:30:05.253',
        'data_type': 'santa:file_system_event',
        'file_path': '/private/var/db/santa/santa.log.5.gz',
        'file_new_path': '/private/var/db/santa/santa.log.6.gz',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'gid': '0',
        'user': 'root',
        'group': 'wheel'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Process exit log
    expected_event_values = {
        'action': 'EXIT',
        'date_time': '2022-02-09 16:47:02.893',
        'pid': '75780',
        'pid_version': '1765713',
        'ppid': '155',
        'uid': '0',
        'gid': '1'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Link file operation event log
    expected_event_values = {
        'action': 'LINK',
        'date_time': '2022-02-17 16:30:05.257',
        'data_type': 'santa:file_system_event',
        'file_path': '/private/var/db/santa/santa.log',
        'file_new_path': '/private/var/db/santa/santa.log.0',
        'pid': '26150',
        'pid_version': '2228280',
        'ppid': '1',
        'process': 'newsyslog',
        'process_path': '/usr/sbin/newsyslog',
        'uid': '0',
        'gid': '0',
        'user': 'root',
        'group': 'wheel'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    # Execution event log
    expected_event_values = {
        'action': 'EXEC',
        'date_time': '2022-02-17 16:31:28.414',
        'data_type': 'santa:execution',
        'decision': 'ALLOW',
        'reason': 'BINARY',
        'long_reason': 'critical system binary',
        'process_hash':
            '25977d1584525b571fc6d19dcac1a768d0555c58777876869255de312dcfcaf3',
        'certificate_hash':
            'd84db96af8c2e60ac4c851a21ec460f6f84e0235beb17d24a78712b9b021ed57',
        'certificate_common_name': 'Software Signing',
        'pid': '26364',
        'pid_version': '2228711',
        'ppid': '1',
        'uid': '0',
        'gid': '0',
        'user': 'root',
        'group': 'wheel',
        'mode': 'M',
        'process_path': '/usr/libexec/xpcproxy',
        'process_arguments': ('xpcproxy '
            'com.apple.mdworker.shared.07000000-0000-0000-0000-000000000000')}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
