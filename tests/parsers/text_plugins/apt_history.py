#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Advanced Packaging Tool (APT) History log text plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import apt_history

from tests.parsers.text_plugins import test_lib


class APTHistoryLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the APT History log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = apt_history.APTHistoryLogTextPlugin()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Start-Date: 2019-07-10  16:38:08\n'
        b'Commandline: apt-get upgrade --no-install-recommends --assume-yes\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = apt_history.APTHistoryLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['apt_history.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': 'Install',
        'command_line': (
            'apt-get -y install python-pip python3-pip python-dev python3-dev '
            'git tmux screen joe'),
        'data_type': 'linux:apt_history_log:entry',
        'end_time': '2019-07-11T12:21:28',
        'packages': (
            'libmpc3:amd64 (1.0.3-1+b2, automatic), '
            'manpages:amd64 (4.10-2, automatic), '
            'libmpx2:amd64 (6.3.0-18+deb9u1, automatic), '
            'python3-dev:amd64 (3.5.3-1), '
            'python2.7-dev:amd64 (2.7.13-2+deb9u3, automatic), '
            'libdbus-1-3:amd64 (1.10.28-0+deb9u1, automatic), '
            'linux-libc-dev:amd64 (4.9.168-1+deb9u3, automatic), '
            'python-xdg:amd64 (0.25-4, automatic), '
            'libmpfr4:amd64 (3.1.5-1, automatic), '
            'sgml-base:amd64 (1.29, automatic), '
            'libgirepository-1.0-1:amd64 (1.50.0-1+b1, automatic), '
            'libfakeroot:amd64 (1.21-3.1, automatic), '
            'libc6-dev:amd64 (2.24-11+deb9u4, automatic), '
            'rename:amd64 (0.20-4, automatic), '
            'git-man:amd64 (1:2.11.0-3+deb9u4, automatic), '
            'xdg-user-dirs:amd64 (0.15-2+b1, automatic), '
            'libexpat1-dev:amd64 (2.2.0-2+deb9u2, automatic), '
            'cpp-6:amd64 (6.3.0-18+deb9u1, automatic), '
            'dbus:amd64 (1.10.28-0+deb9u1, automatic), '
            'libalgorithm-diff-perl:amd64 (1.19.03-1, automatic), '
            'python-gi:amd64 (3.22.0-2, automatic), '
            'libalgorithm-merge-perl:amd64 (0.08-3, automatic), '
            'libicu57:amd64 (57.1-6+deb9u2, automatic), '
            'binutils:amd64 (2.28-5, automatic), '
            'cpp:amd64 (4:6.3.0-4, automatic), '
            'python-dbus:amd64 (1.2.4-1+b1, automatic), '
            'libitm1:amd64 (6.3.0-18+deb9u1, automatic), '
            'libpython-all-dev:amd64 (2.7.13-2, automatic), '
            'g++:amd64 (4:6.3.0-4, automatic), '
            'perl-modules-5.24:amd64 (5.24.1-3+deb9u5, automatic), '
            'libpython2.7:amd64 (2.7.13-2+deb9u3, automatic), '
            'python3-pip:amd64 (9.0.1-2+deb9u1), '
            'python3-keyring:amd64 (10.1-1, automatic), '
            'python3-wheel:amd64 (0.29.0-2, automatic), '
            'libpython3.5:amd64 (3.5.3-1+deb9u1, automatic), '
            'gcc:amd64 (4:6.3.0-4, automatic), '
            'git:amd64 (1:2.11.0-3+deb9u4), '
            'python3-idna:amd64 (2.2-1, automatic), '
            'libpython2.7-dev:amd64 (2.7.13-2+deb9u3, automatic), '
            'libcilkrts5:amd64 (6.3.0-18+deb9u1, automatic), '
            'python3-six:amd64 (1.10.0-3, automatic), '
            'libasan3:amd64 (6.3.0-18+deb9u1, automatic), '
            'libquadmath0:amd64 (6.3.0-18+deb9u1, automatic), '
            'python3.5-dev:amd64 (3.5.3-1+deb9u1, automatic), '
            'joe:amd64 (4.4-1), '
            'libisl15:amd64 (0.18-1, automatic), '
            'python-enum34:amd64 (1.1.6-1, automatic), '
            'build-essential:amd64 (12.3, automatic), '
            'libfile-fcntllock-perl:amd64 (0.22-3+b2, automatic), '
            'python3-xdg:amd64 (0.25-4, automatic), '
            'libperl5.24:amd64 (5.24.1-3+deb9u5, automatic), '
            'python-cryptography:amd64 (1.7.1-3+deb9u1, automatic), '
            'python-crypto:amd64 (2.6.1-7, automatic), '
            'xml-core:amd64 (0.17, automatic), '
            'python-keyrings.alt:amd64 (1.3-1, automatic), '
            'python-cffi-backend:amd64 (1.9.1-2, automatic), '
            'python-ipaddress:amd64 (1.0.17-1, automatic), '
            'libtsan0:amd64 (6.3.0-18+deb9u1, automatic), '
            'libgcc-6-dev:amd64 (6.3.0-18+deb9u1, automatic), '
            'python3-cryptography:amd64 (1.7.1-3+deb9u1, automatic), '
            'libubsan0:amd64 (6.3.0-18+deb9u1, automatic), '
            'gir1.2-glib-2.0:amd64 (1.50.0-1+b1, automatic), '
            'g++-6:amd64 (6.3.0-18+deb9u1, automatic), '
            'libpython-dev:amd64 (2.7.13-2, automatic), '
            'python3-cffi-backend:amd64 (1.9.1-2, automatic), '
            'make:amd64 (4.1-9.1, automatic), '
            'fakeroot:amd64 (1.21-3.1, automatic), '
            'gcc-6:amd64 (6.3.0-18+deb9u1, automatic), '
            'python-all:amd64 (2.7.13-2, automatic), '
            'liblsan0:amd64 (6.3.0-18+deb9u1, automatic), '
            'shared-mime-info:amd64 (1.8-1+deb9u1, automatic), '
            'libgomp1:amd64 (6.3.0-18+deb9u1, automatic), '
            'libpython3.5-dev:amd64 (3.5.3-1+deb9u1, automatic), '
            'libdbus-glib-1-2:amd64 (0.108-2, automatic), '
            'libutempter0:amd64 (1.1.6-3, automatic), '
            'python-secretstorage:amd64 (2.3.1-2, automatic), '
            'python-dev:amd64 (2.7.13-2), '
            'python-pyasn1:amd64 (0.1.9-2, automatic), '
            'python-setuptools:amd64 (33.1.1-1, automatic), '
            'python-keyring:amd64 (10.1-1, automatic), '
            'manpages-dev:amd64 (4.10-2, automatic), '
            'bzip2:amd64 (1.0.6-8.1, automatic), '
            'python3-dbus:amd64 (1.2.4-1+b1, automatic), '
            'libevent-2.0-5:amd64 (2.0.21-stable-3, automatic), '
            'libglib2.0-data:amd64 (2.50.3-2, automatic), '
            'python3-keyrings.alt:amd64 (1.3-1, automatic), '
            'libc-dev-bin:amd64 (2.24-11+deb9u4, automatic), '
            'libxml2:amd64 (2.9.4+dfsg1-2.2+deb9u2, automatic), '
            'python3-gi:amd64 (3.22.0-2, automatic), '
            'python3-crypto:amd64 (2.6.1-7, automatic), '
            'perl:amd64 (5.24.1-3+deb9u5, automatic), '
            'rsync:amd64 (3.1.2-1+deb9u2, automatic), '
            'tmux:amd64 (2.3-4), '
            'python-idna:amd64 (2.2-1, automatic), '
            'python-wheel:amd64 (0.29.0-2, automatic), '
            'libpython3-dev:amd64 (3.5.3-1, automatic), '
            'libatomic1:amd64 (6.3.0-18+deb9u1, automatic), '
            'libcc1-0:amd64 (6.3.0-18+deb9u1, automatic), '
            'libdpkg-perl:amd64 (1.18.25, automatic), '
            'patch:amd64 (2.7.5-1+deb9u1, automatic), '
            'python3-secretstorage:amd64 (2.3.1-2, automatic), '
            'libalgorithm-diff-xs-perl:amd64 (0.04-4+b2, automatic), '
            'python-pip-whl:amd64 (9.0.1-2+deb9u1, automatic), '
            'libglib2.0-0:amd64 (2.50.3-2, automatic), '
            'python-pip:amd64 (9.0.1-2+deb9u1), '
            'libcurl3-gnutls:amd64 (7.52.1-5+deb9u9, automatic), '
            'less:amd64 (481-2.1, automatic), '
            'python3-setuptools:amd64 (33.1.1-1, automatic), '
            'dpkg-dev:amd64 (1.18.25, automatic), '
            'python-all-dev:amd64 (2.7.13-2, automatic), '
            'python3-pyasn1:amd64 (0.1.9-2, automatic), '
            'libstdc++-6-dev:amd64 (6.3.0-18+deb9u1, automatic), '
            'liberror-perl:amd64 (0.17024-1, automatic)'),
        'start_time': '2019-07-11T12:20:55'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
