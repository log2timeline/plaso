#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the syslog text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import syslog

from tests.parsers.text_plugins import test_lib


class SyslogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the syslog text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = syslog.SyslogTextPlugin()

    # Check ChromeOS syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2016-10-25T12:37:23.297265-07:00 INFO periodic_scheduler[13707]: '
        b'cleanup_logs: job completed\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2020-05-31T00:00:45.738158+00:00 localhost systemd[1]: Reloaded '
        b'System Logging Service.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check protocol 23 rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'<30>1 2021-03-06T04:07:38.265422+00:00 hostname systemd 1 - -  '
        b'Started Regular background program processing daemon.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check traditional syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in \xc3\xadmynd.dd.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check traditional rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Jan 22 07:54:32 myhostname.myhost.com Job `cron.daily\' '
        b'terminated\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check syslogkd rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Mar  6 04:07:28 hostname systemd[1]: Started Regular background '
        b'program processing daemon.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check non-syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'gpgv: Signature made Wed Oct 22 17:40:30 2014 UTC using DSA key ID '
        b'437D05B5\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

  def testProcessChromeOS(self):
    """Tests the Process function with a ChromeOS syslog file."""
    plugin = syslog.SyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog_chromeos'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'cleanup_logs: job completed',
        'data_type': 'syslog:line',
        'last_written_time': '2016-10-25T12:37:23.297265-07:00',
        'pid': 13707,
        'reporter': 'periodic_scheduler',
        'severity': 'INFO'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessRsyslog(self):
    """Tests the Process function with a rsyslog file."""
    plugin = syslog.SyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog_rsyslog'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'localhost',
        'last_written_time': '2020-05-31T00:00:45.698463+00:00',
        'reporter': 'rsyslogd',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessRsyslogProtocol23(self):
    """Tests the Process function with a protocol 23 rsyslog file."""
    plugin = syslog.SyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['syslog_rsyslog_SyslogProtocol23Format'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'hostname',
        'last_written_time': '2021-03-06T04:07:38.251122+00:00',
        'reporter': 'log_tag',
        'severity': 'DEBUG'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TraditionalSyslogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the traditional syslog text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = syslog.TraditionalSyslogTextPlugin()

    # Check traditional syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in \xc3\xadmynd.dd.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check syslogkd rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Mar  6 04:07:28 hostname systemd[1]: Started Regular background '
        b'program processing daemon.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check traditional rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Jan 22 07:54:32 myhostname.myhost.com Job `cron.daily\' '
        b'terminated\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check ChromeOS syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2016-10-25T12:37:23.297265-07:00 INFO periodic_scheduler[13707]: '
        b'cleanup_logs: job completed\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2020-05-31T00:00:45.738158+00:00 localhost systemd[1]: Reloaded '
        b'System Logging Service.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check protocol 23 rsyslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'<30>1 2021-03-06T04:07:38.265422+00:00 hostname systemd 1 - -  '
        b'Started Regular background program processing daemon.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # Check non-syslog format.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'gpgv: Signature made Wed Oct 22 17:40:30 2014 UTC using DSA key ID '
        b'437D05B5\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 16)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'INFO No new content in ímynd.dd.',
        'data_type': 'syslog:line',
        'hostname': 'myhostname.myhost.com',
        'last_written_time': '0000-01-22T07:52:33',
        'pid': 30840,
        'reporter': 'client',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check if year is incremented.
    expected_event_values = {
        'body': 'This syslog message has a fractional value for seconds.',
        'data_type': 'syslog:line',
        'last_written_time': '0001-03-23T23:01:18',
        'reporter': 'somrandomexe',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 9)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessCron(self):
    """Tests the Process function with a cron syslog file."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog_cron.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': 'sleep $(( 1 * 60 )); touch /tmp/afile.txt',
        'data_type': 'syslog:cron:task_run',
        'last_written_time': '0000-03-11T19:26:39',
        'username': 'root'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessDarwin(self):
    """Tests the Process function with a Darwin syslog file."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog_osx'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'osx-machine',
        'last_written_time': '0000-03-11T19:26:39',
        'reporter': 'kernel',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessRsyslogSysklogd(self):
    """Tests the Process function with a syslogkd rsyslog file."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['syslog_rsyslog_SysklogdFileFormat'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'hostname',
        'last_written_time': '0000-03-06T04:07:28',
        'reporter': 'log_tag',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessRsyslogTraditional(self):
    """Tests the Process function with a traditional rsyslog file."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['syslog_rsyslog_traditional'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'myhostname.myhost.com',
        'last_written_time': '0000-01-22T07:54:32',
        'reporter': 'Job',
        'severity': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessSshd(self):
    """Tests the Process function with a sshd syslog file."""
    plugin = syslog.TraditionalSyslogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['syslog_ssh.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'last_written_time': '0000-03-11T00:00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': (
            'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
            'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99'),
        'data_type': 'syslog:ssh:login',
        'fingerprint': 'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99',
        'ip_address': '192.168.0.1',
        'last_written_time': '0000-03-11T19:26:39'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:ssh:failed_connection',
        'ip_address': '001:db8:a0b:12f0::1',
        'last_written_time': '0000-03-11T22:55:30',
        'port': '8759'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:ssh:opened_connection',
        'ip_address': '188.124.3.41',
        'last_written_time': '0000-03-11T22:55:31'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
