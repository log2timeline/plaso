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

    def testProcessCronDebian(self):
        """Tests the Process function with Debian cron daemon and crontab messages."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_cron_debian.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 15)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_data_types = [
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:task_run",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:task_run",
            "syslog:cron:entry",
        ]
        for index, expected_data_type in enumerate(expected_data_types):
            event_data = storage_writer.GetAttributeContainerByIndex(
                "event_data", index
            )
            self.assertEqual(event_data.data_type, expected_data_type, index)

        # cron[1615]: (CRON) INFO (pidfile fd = 3)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "pidfile fd = 3",
            "event_type": "INFO",
            "last_written_time": "2026-10-10T11:45:20.510482+00:00",
            "reporter": "cron",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # CRON[1682]: (svc-backup) CMD (/usr/local/bin/agent --daemon)
        expected_event_values = {
            "command": "/usr/local/bin/agent --daemon",
            "data_type": "syslog:cron:task_run",
            "last_written_time": "2026-10-10T11:45:20.972191+00:00",
            "reporter": "CRON",
            "username": "svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # crontab[2436]: (ubuntu) REPLACE (ubuntu)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "ubuntu",
            "event_type": "REPLACE",
            "reporter": "crontab",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

        # cron[1615]: (ubuntu) RELOAD (crontabs/ubuntu)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "crontabs/ubuntu",
            "event_type": "RELOAD",
            "reporter": "cron",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

        # cron[2478]: (*system*plaso-capture) RELOAD (/etc/cron.d/plaso-capture)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "/etc/cron.d/plaso-capture",
            "event_type": "RELOAD",
            "username": "*system*plaso-capture",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 14)
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

    def testProcessSshdConnectionEnd(self):
        """Tests the Process function with sshd connection end messages."""
        plugin = syslog.SyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_sshd_connection_end.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 23)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_data_types = [
            "syslog:ssh:closed_connection",
            "syslog:ssh:received_disconnect",
            "syslog:ssh:closed_connection",
            "syslog:line",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
            "syslog:ssh:invalid_user",
            "syslog:ssh:closed_connection",
            "syslog:ssh:login",
            "syslog:ssh:received_disconnect",
            "syslog:ssh:closed_connection",
            "syslog:ssh:invalid_user",
            "syslog:ssh:failed_connection",
            "syslog:ssh:received_disconnect",
            "syslog:ssh:closed_connection",
            "syslog:ssh:failed_connection",
            "syslog:ssh:received_disconnect",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
            "syslog:ssh:closed_connection",
        ]
        for index, expected_data_type in enumerate(expected_data_types):
            event_data = storage_writer.GetAttributeContainerByIndex(
                "event_data", index
            )
            self.assertEqual(event_data.data_type, expected_data_type, index)

        # Connection closed by authenticating user svc-backup 192.168.1.92 port
        # 38204 [preauth]
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.1.92",
            "is_authenticated": False,
            "is_invalid_user": False,
            "last_written_time": "2026-07-28T18:57:09.958129+00:00",
            "port": "38204",
            "reporter": "sshd-session",
            "username": "svc-backup",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Received disconnect from 192.168.137.1 port 63234:11: disconnected by user
        expected_event_values = {
            "data_type": "syslog:ssh:received_disconnect",
            "disconnect_reason": "disconnected by user",
            "disconnect_reason_code": 11,
            "ip_address": "192.168.137.1",
            "last_written_time": "2026-07-26T13:03:24.719663+00:00",
            "port": "63234",
            "reporter": "sshd-session",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Disconnected from user ubuntu 192.168.137.1 port 63234
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.137.1",
            "is_authenticated": True,
            "is_invalid_user": False,
            "port": "63234",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        # Connection reset by 192.168.248.1 port 60274
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.248.1",
            "is_authenticated": None,
            "is_invalid_user": None,
            "port": "60274",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # Timeout, client not responding from user ubuntu 192.168.248.1 port 55307
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.248.1",
            "is_authenticated": True,
            "port": "55307",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
        self.CheckEventData(event_data, expected_event_values)

        # Timeout before authentication for connection from 192.168.248.1 to
        # 192.168.248.128, pid = 2903
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.248.1",
            "is_authenticated": None,
            "port": None,
            "reporter": "sshd",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

        # Invalid user john doe from 192.168.248.1 port 54928
        expected_event_values = {
            "data_type": "syslog:ssh:invalid_user",
            "ip_address": "192.168.248.1",
            "last_written_time": "2026-10-08T00:19:26.539626+00:00",
            "port": "54928",
            "username": "john doe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

        # Connection closed by invalid user john doe 192.168.248.1 port 54928
        # [preauth]
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.248.1",
            "is_authenticated": False,
            "is_invalid_user": True,
            "port": "54928",
            "username": "john doe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 9)
        self.CheckEventData(event_data, expected_event_values)

        # Accepted publickey for ubuntu from fe80::621:e520:10d6:6621%ens36 port
        # 54931 ssh2: ED25519 SHA256:a79QfkCiaM8pEpw/wmP0Qfkl3ttsHxPlSKgqilMv9K8
        expected_event_values = {
            "authentication_method": "publickey",
            "data_type": "syslog:ssh:login",
            "fingerprint": "ED25519 SHA256:a79QfkCiaM8pEpw/wmP0Qfkl3ttsHxPlSKgqilMv9K8",
            "ip_address": "fe80::621:e520:10d6:6621%ens36",
            "port": "54931",
            "username": "ubuntu",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 10)
        self.CheckEventData(event_data, expected_event_values)

        # error: Received disconnect from 192.168.248.1 port 54936:14: No more
        # authentication methods available [preauth]
        expected_event_values = {
            "data_type": "syslog:ssh:received_disconnect",
            "disconnect_reason": "No more authentication methods available",
            "disconnect_reason_code": 14,
            "ip_address": "192.168.248.1",
            "port": "54936",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 15)
        self.CheckEventData(event_data, expected_event_values)

        # Disconnected from invalid user nosuchuser 192.168.248.1 port 54936
        # [preauth]
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "is_authenticated": False,
            "is_invalid_user": True,
            "port": "54936",
            "username": "nosuchuser",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 16)
        self.CheckEventData(event_data, expected_event_values)

        # Read error from remote host 192.168.248.1 port 54939: Connection reset
        # by peer
        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.248.1",
            "is_authenticated": None,
            "port": "54939",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 20)
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
            "data_type": "syslog:cron:entry",
            "detail": "1.7.2",
            "event_type": "STARTUP",
            "last_written_time": "0000-07-07T20:56:16",
            "message_body": "(CRON) STARTUP (1.7.2)",
            "pid": 1276,
            "reporter": "crond",
            "username": None,
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
            "data_type": "syslog:run_parts:script_start",
            "directory": "/etc/cron.hourly",
            "last_written_time": "0000-07-07T21:01:00",
            "message_body": "(/etc/cron.hourly) starting 0anacron",
            "reporter": "run-parts",
            "script_name": "0anacron",
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

    def testProcessCronie(self):
        """Tests the Process function with cronie, crontab, run-parts and anacron."""
        plugin = syslog.TraditionalSyslogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["syslog", "syslog_cronie.log"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 33)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_data_types = [
            "syslog:cron:entry",
            "syslog:line",
            "syslog:line",
            "syslog:line",
            "syslog:anacron:job_start",
            "syslog:anacron:job_end",
            "syslog:line",
            "syslog:line",
            "syslog:line",
            "syslog:line",
            "syslog:line",
            "syslog:anacron:job_start",
            "syslog:run_parts:script_start",
            "syslog:run_parts:script_end",
            "syslog:anacron:job_end",
            "syslog:line",
            "syslog:line",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
            "syslog:cron:entry",
        ]
        for index, expected_data_type in enumerate(expected_data_types):
            event_data = storage_writer.GetAttributeContainerByIndex(
                "event_data", index
            )
            self.assertEqual(event_data.data_type, expected_data_type, index)

        # crontab[1578]: (root) REPLACE (root)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "root",
            "event_type": "REPLACE",
            "last_written_time": "0000-10-10T06:44:29",
            "reporter": "crontab",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # anacron[1588]: Job `plaso-fail' started
        expected_event_values = {
            "data_type": "syslog:anacron:job_start",
            "job_identifier": "plaso-fail",
            "last_written_time": "0000-10-10T06:44:39",
            "reporter": "anacron",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # anacron[1588]: Job `plaso-fail' terminated (exit status: 3) (produced output)
        expected_event_values = {
            "data_type": "syslog:anacron:job_end",
            "exit_status": 3,
            "job_identifier": "plaso-fail",
            "reporter": "anacron",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        # run-parts[1601]: (/etc/cron.daily) starting zz-plaso-fail
        expected_event_values = {
            "data_type": "syslog:run_parts:script_start",
            "directory": "/etc/cron.daily",
            "last_written_time": "0000-10-10T06:44:42",
            "reporter": "run-parts",
            "script_name": "zz-plaso-fail",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 12)
        self.CheckEventData(event_data, expected_event_values)

        # run-parts[1605]: (/etc/cron.daily) finished zz-plaso-fail
        expected_event_values = {
            "data_type": "syslog:run_parts:script_end",
            "directory": "/etc/cron.daily",
            "script_name": "zz-plaso-fail",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 13)
        self.CheckEventData(event_data, expected_event_values)

        # anacron[1595]: Job `cron.daily' terminated (produced output)
        expected_event_values = {
            "data_type": "syslog:anacron:job_end",
            "exit_status": 0,
            "job_identifier": "cron.daily",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 14)
        self.CheckEventData(event_data, expected_event_values)

        # crond[1608]: (CRON) STARTUP (1.7.2)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "1.7.2",
            "event_type": "STARTUP",
            "reporter": "crond",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18)
        self.CheckEventData(event_data, expected_event_values)

        # crond[1608]: (*system*) RELOAD (/etc/cron.d/0hourly)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "/etc/cron.d/0hourly",
            "event_type": "RELOAD",
            "username": "*system*",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 25)
        self.CheckEventData(event_data, expected_event_values)

        # crontab[1781]: (root) BEGIN EDIT (root)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "root",
            "event_type": "BEGIN EDIT",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 28)
        self.CheckEventData(event_data, expected_event_values)

        # crond[1608]: (root) RELOAD (/var/spool/cron/root)
        expected_event_values = {
            "data_type": "syslog:cron:entry",
            "detail": "/var/spool/cron/root",
            "event_type": "RELOAD",
            "last_written_time": "0000-10-10T06:48:00",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 30)
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

        expected_event_values = {
            "data_type": "syslog:ssh:received_disconnect",
            "disconnect_reason": "disconnected by user",
            "disconnect_reason_code": 11,
            "ip_address": "192.168.1.62",
            "last_written_time": "0000-08-02T11:42:18",
            "port": "60218",
            "reporter": "sshd-session",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "syslog:ssh:closed_connection",
            "ip_address": "192.168.1.62",
            "is_authenticated": True,
            "is_invalid_user": False,
            "last_written_time": "0000-08-02T11:42:18",
            "port": "60218",
            "reporter": "sshd-session",
            "username": "root",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
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


if __name__ == "__main__":
    unittest.main()
