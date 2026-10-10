#!/usr/bin/env python3
"""Tests for the syslog text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import syslog

from tests.parsers.text_plugins import test_lib


class SyslogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the syslog text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = syslog.SyslogTextPlugin()

        # Check ChromeOS syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"2016-10-25T12:37:23.297265-07:00 INFO periodic_scheduler[13707]: "
            b"cleanup_logs: job completed\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"2020-05-31T00:00:45.738158+00:00 localhost systemd[1]: Reloaded "
            b"System Logging Service.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check protocol 23 rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"<30>1 2021-03-06T04:07:38.265422+00:00 hostname systemd 1 - -  "
            b"Started Regular background program processing daemon.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check traditional syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
                b"content in \xc3\xadmynd.dd.\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check traditional rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"Jan 22 07:54:32 myhostname.myhost.com Job `cron.daily' "
                b"terminated\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check syslogkd rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"Mar  6 04:07:28 hostname systemd[1]: Started Regular background "
                b"program processing daemon.\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check non-syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile(
            "/file.txt",
            (
                b"gpgv: Signature made Wed Oct 22 17:40:30 2014 UTC using DSA key ID "
                b"437D05B5\n"
            ),
        )

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

    def testProcessChromeOS(self):
        """Tests the Process function with a ChromeOS syslog file."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_chromeos"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "2016-10-25T12:37:23.297265-07:00",
            "message_body": "cleanup_logs: job completed",
            "pid": 13707,
            "reporter": "periodic_scheduler",
            "severity": "INFO",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessRsyslog(self):
        """Tests the Process function with a rsyslog file."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_rsyslog"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "hostname": "localhost",
            "last_written_time": "2020-05-31T00:00:45.698463+00:00",
            "reporter": "rsyslogd",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessRsyslogProtocol23(self):
        """Tests the Process function with a protocol 23 rsyslog file."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_rsyslog_SyslogProtocol23Format"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "facility": "user-level message",
            "hostname": "hostname",
            "last_written_time": "2021-03-06T04:07:38.251122+00:00",
            "message_identifier": "123",
            "reporter": "log_tag",
            "severity": "DEBUG",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessSudo(self):
        """Tests the Process function with a sudo syslog file."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_sudo.log"], plugin
        )
        # The file has 29 records, of which the last two are one command that sudo
        # split into a command record and a "(command continued)" record.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 28)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A pam_unix session record.
        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "2026-07-26T13:03:25.681173+00:00",
            "reporter": "sudo",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A sudo-rs command record, which has no TTY= field and two spaces after
        # the user name.
        expected_event_values = {
            "account": "root",
            "command_line": "/usr/sbin/auditctl -D",
            "data_type": "syslog:sudo:command",
            "group_name": None,
            "last_written_time": "2026-07-26T13:03:25.682007+00:00",
            "reporter": "sudo",
            "terminal": None,
            "username": "ubuntu",
            "working_directory": "/home/ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # A command line with a trailing space, as sudo-rs writes it without
        # arguments.
        expected_event_values = {
            "command_line": "/usr/bin/true ",
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-28T12:10:50.432238+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)

        # A command line with escaped double quotes, stored as logged.
        expected_event_values = {
            "command_line": (
                '/usr/bin/python3 -c import json;d=json.load(open(\\"/var/lib/snapd/'
                'state.json\\"));print(sorted(d.keys()));print(json.dumps(d,indent=1)'
                "[:1800])"
            ),
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-28T12:12:44.009943+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 13)
        self.CheckEventData(event_data, expected_event_values)

        # A command record with a TTY= field.
        expected_event_values = {
            "account": "root",
            "command_line": "/usr/bin/id -un",
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-28T22:17:25.893483+00:00",
            "terminal": "pts/0",
            "username": "svc-backup",
            "working_directory": "/home/svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 17)
        self.CheckEventData(event_data, expected_event_values)

        # A denied command record, which carries a reason before the fields, is
        # not a command record.
        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "2026-07-28T22:17:31.279993+00:00",
            "message_body": (
                "john.doe : user NOT in sudoers ; TTY=pts/0 ; PWD=/home/john.doe ; "
                "USER=root ; COMMAND=/usr/bin/id"
            ),
            "reporter": "sudo",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18)
        self.CheckEventData(event_data, expected_event_values)

        # A command record where sudo padded the user name to 8 characters.
        expected_event_values = {
            "command_line": "/usr/bin/id -un",
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-29T10:36:29.167005+00:00",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 21)
        self.CheckEventData(event_data, expected_event_values)

        # A command line with a quoted argument containing an escaped single quote
        # and an escaped backslash, stored as logged.
        expected_event_values = {
            "command_line": "/bin/echo 'it\\'s a \\\\ test'",
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-29T10:36:29.308488+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 26)
        self.CheckEventData(event_data, expected_event_values)

        # A command that sudo split into two records, joined into one event that
        # carries the date and time of the first record.
        expected_event_values = {
            "data_type": "syslog:sudo:command",
            "last_written_time": "2026-07-29T10:36:29.418533+00:00",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 27)
        self.CheckEventData(event_data, expected_event_values)

        arguments = event_data.command_line.split(" ")
        self.assertEqual(len(arguments), 201)
        self.assertEqual(arguments[0], "/bin/echo")
        self.assertEqual(arguments[1], "arg0000")
        self.assertEqual(arguments[112], "arg0111")
        self.assertEqual(arguments[113], "arg0112")
        self.assertEqual(arguments[200], "arg0199")


class TraditionalSyslogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the traditional syslog text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = syslog.TraditionalSyslogTextPlugin()

        # Check traditional syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in \xc3\xadmynd.dd.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check syslogkd rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"Mar  6 04:07:28 hostname systemd[1]: Started Regular background "
            b"program processing daemon.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check traditional rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"Jan 22 07:54:32 myhostname.myhost.com Job `cron.daily' " b"terminated\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(result)

        # Check ChromeOS syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"2016-10-25T12:37:23.297265-07:00 INFO periodic_scheduler[13707]: "
            b"cleanup_logs: job completed\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"2020-05-31T00:00:45.738158+00:00 localhost systemd[1]: Reloaded "
            b"System Logging Service.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check protocol 23 rsyslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"<30>1 2021-03-06T04:07:38.265422+00:00 hostname systemd 1 - -  "
            b"Started Regular background program processing daemon.\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

        # Check non-syslog format.
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        data = (
            b"gpgv: Signature made Wed Oct 22 17:40:30 2014 UTC using DSA key ID "
            b"437D05B5\n"
        )
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertFalse(result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["syslog", "syslog"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 16)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "facility": None,
            "hostname": "myhostname.myhost.com",
            "last_written_time": "0000-01-22T07:52:33",
            "message_body": "INFO No new content in ímynd.dd.",
            "pid": 30840,
            "reporter": "client",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Check if year is incremented.
        expected_event_values = {
            "data_type": "syslog:line",
            "facility": None,
            "last_written_time": "0001-03-23T23:01:18",
            "message_body": "This syslog message has a fractional value for seconds.",
            "reporter": "somrandomexe",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessCron(self):
        """Tests the Process function with a cron syslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_cron.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "command": "sleep $(( 1 * 60 )); touch /tmp/afile.txt",
            "data_type": "syslog:cron:task_run",
            "last_written_time": "0000-03-11T19:26:39",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessCrond(self):
        """Tests the Process function with a cronie cron log file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_crond.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 42)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # The daemon writes its own messages under the lower case reporter name.
        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "0000-07-07T20:56:16",
            "message_body": "(CRON) STARTUP (1.7.2)",
            "pid": 1276,
            "reporter": "crond",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "command": "run-parts /etc/cron.hourly",
            "data_type": "syslog:cron:task_run",
            "last_written_time": "0000-07-07T21:01:00",
            "pid": 1396,
            "reporter": "CROND",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "0000-07-07T21:01:00",
            "message_body": "(/etc/cron.hourly) starting 0anacron",
            "reporter": "run-parts",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "command": "run-parts /etc/cron.hourly",
            "data_type": "syslog:cron:task_end",
            "last_written_time": "0000-07-07T21:01:00",
            "pid": 1395,
            "reporter": "CROND",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 12)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessDarwin(self):
        """Tests the Process function with a Darwin syslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["syslog", "syslog_osx"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "facility": None,
            "hostname": "osx-machine",
            "last_written_time": "0000-03-11T19:26:39",
            "reporter": "kernel",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessRsyslogSysklogd(self):
        """Tests the Process function with a syslogkd rsyslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_rsyslog_SysklogdFileFormat"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "hostname": "hostname",
            "last_written_time": "0000-03-06T04:07:28",
            "reporter": "log_tag",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessRsyslogTraditional(self):
        """Tests the Process function with a traditional rsyslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_rsyslog_traditional"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "facility": None,
            "hostname": "myhostname.myhost.com",
            "last_written_time": "0000-01-22T07:54:32",
            "reporter": "Job",
            "severity": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessSshd(self):
        """Tests the Process function with a sshd syslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_ssh.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "0000-03-11T00:00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:login",
            "fingerprint": "RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99",
            "ip_address": "192.168.0.1",
            "last_written_time": "0000-03-11T19:26:39",
            "message_body": (
                "Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: "
                "RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:failed_connection",
            "ip_address": "001:db8:a0b:12f0::1",
            "last_written_time": "0000-03-11T22:55:30",
            "port": "8759",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:opened_connection",
            "ip_address": "188.124.3.41",
            "last_written_time": "0000-03-11T22:55:31",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "authentication_method": "password",
            "data_type": "syslog:ssh:failed_connection",
            "ip_address": "188.124.3.41",
            "is_invalid_user": False,
            "last_written_time": "0000-03-11T22:55:32",
            "port": "32889",
            "protocol": "ssh2",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "authentication_method": "publickey",
            "data_type": "syslog:ssh:login",
            "fingerprint": ("RSA SHA256:5xyQ+PG1Z3CIiShclJ2iNya5TOdKDgE/HrOXr21IdOo"),
            "ip_address": "192.0.2.60",
            "last_written_time": "0000-03-11T22:55:35",
            "port": "59915",
            "username": "fred",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

        # Unsuccessful authentication for a user name that does not resolve to an
        # account, which sshd writes with "invalid user" before the name.
        expected_event_values = {
            "authentication_method": "password",
            "data_type": "syslog:ssh:failed_connection",
            "ip_address": "192.168.1.92",
            "is_invalid_user": True,
            "last_written_time": "0000-07-28T22:16:48",
            "port": "35932",
            "protocol": "ssh2",
            "username": "admin",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessSshdSession(self):
        """Tests the Process function with a sshd-session syslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_sshd_session.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "authentication_method": "password",
            "data_type": "syslog:ssh:failed_connection",
            "ip_address": "192.168.1.62",
            "last_written_time": "0000-08-02T11:41:04",
            "port": "60203",
            "protocol": "ssh2",
            "reporter": "sshd-session",
            "username": "svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:failed_connection",
            "last_written_time": "0000-08-02T11:41:08",
            "reporter": "sshd-session",
            "username": "john.doe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:login",
            "last_written_time": "0000-08-02T11:42:13",
            "reporter": "sshd-session",
            "username": "svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:login",
            "last_written_time": "0000-08-02T11:42:16",
            "reporter": "sshd-session",
            "username": "test_user",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # A message that the sshd structures do not define, which is retained as
        # a syslog:line.
        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "0000-08-02T11:42:18",
            "reporter": "sshd-session",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "authentication_method": "publickey",
            "data_type": "syslog:ssh:login",
            "fingerprint": (
                "ED25519 SHA256:a79QfkCiaM8pEpw/wmP0Qfkl3ttsHxPlSKgqilMv9K8"
            ),
            "ip_address": "192.168.1.62",
            "last_written_time": "0000-08-02T11:42:48",
            "port": "60220",
            "protocol": "ssh2",
            "reporter": "sshd-session",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessSudo(self):
        """Tests the Process function with a sudo syslog file."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_sudo_traditional.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "account": "root",
            "command_line": "/usr/bin/id -un",
            "data_type": "syslog:sudo:command",
            "last_written_time": "0000-07-28T14:06:52",
            "pid": 3824,
            "reporter": "sudo",
            "terminal": "pts/1",
            "username": "svc-backup",
            "working_directory": "/home/svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # A denied command record is not a command record.
        expected_event_values = {
            "data_type": "syslog:line",
            "last_written_time": "0000-07-28T14:06:57",
            "pid": 3870,
            "reporter": "sudo",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        # A command record where sudo padded the user name to 8 characters, with
        # a control character in the command line stored as logged.
        expected_event_values = {
            "command_line": "/bin/echo x#011hey",
            "data_type": "syslog:sudo:command",
            "last_written_time": "0000-07-29T05:37:17",
            "pid": 1762,
            "terminal": None,
            "username": "root",
            "working_directory": "/root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

        # The last record of the file is a command record.
        expected_event_values = {
            "command_line": "/usr/bin/id -un",
            "data_type": "syslog:sudo:command",
            "pid": 1765,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

    def _ProcessByteStream(self, plugin, data):
        """Parses an in-memory byte stream with a traditional syslog plugin.

        Args:
          plugin (TextPlugin): text log file plugin.
          data (bytes): contents of the log file to parse.

        Returns:
          FakeStorageWriter: storage writer.
        """
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile("/file.txt", data)

        file_entry = file_system_builder.file_system.GetFileEntryByPath("/file.txt")

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )
        parser_mediator.AppendToParserChain("text")

        file_object = file_entry.GetFileObject()
        text_reader = text_parser.EncodedTextReader(file_object, encoding="utf-8")
        text_reader.ReadLines()

        required_format = plugin.CheckRequiredFormat(parser_mediator, text_reader)
        self.assertTrue(required_format)

        plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

        return storage_writer

    def testProcessComment(self):
        """Tests the Process function with a syslog comment line."""
        plugin = syslog.TraditionalSyslogTextPlugin()

        data = (
            b"Jan 22 07:54:32 myhostname client[30840]: starting up\n"
            b"Jan 22 07:54:32: --- last message repeated 5 times ---\n"
        )

        storage_writer = self._ProcessByteStream(plugin, data)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        expected_event_values = {
            "data_type": "syslog:line",
            "message_body": "last message repeated 5 times ---",
            "reporter": "---",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessLongComment(self):
        """Tests the Process function with a long syslog comment line.

        Bounding the comment-body scan to the current line leaves the parsed
        message body unchanged, whether the comment body is short or long. This
        parses a long comment line and checks that it produces the same event
        data structure and message body as the short comment line parsed by
        testProcessComment.
        """
        plugin = syslog.TraditionalSyslogTextPlugin()

        comment_body = ("the quick brown fox jumps over the lazy dog " * 200).strip()

        data = (
            b"Jan 22 07:54:32 myhostname client[30840]: starting up\n"
            + f"Jan 22 07:54:32: --- {comment_body} ---\n".encode("utf-8")
        )

        storage_writer = self._ProcessByteStream(plugin, data)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        expected_event_values = {
            "data_type": "syslog:line",
            "message_body": f"{comment_body} ---",
            "reporter": "---",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
