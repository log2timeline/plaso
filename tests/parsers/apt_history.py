#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Advanced Packaging Tool (APT) History log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import apt_history as _  # pylint: disable=unused-import
from plaso.lib import errors
from plaso.parsers import apt_history

from tests.parsers import test_lib


class APTHistoryLogUnitTest(test_lib.ParserTestCase):
  """Tests for the APT History log parser.

  Since APT History logs record in local time, these tests assume that the local
  timezone is set to UTC.
  """

  def testParseLog(self):
    """Tests the Parse function on apt_history.log."""
    parser = apt_history.APTHistoryLogParser()
    storage_writer = self._ParseFile(['apt_history.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2019-07-10 16:38:08.000000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2019-07-10 16:38:12.000000')

    event = events[2]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.CheckTimestamp(event.timestamp, '2019-07-11 12:20:55.000000')

    expected_message = (
        'Install: libmpc3:amd64 (1.0.3-1+b2, automatic), '
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
        'liberror-perl:amd64 (0.17024-1, automatic) '
        '[Commandline: apt-get -y install python-pip python3-pip python-dev '
        'python3-dev git tmux screen joe]')
    expected_short_message = (
        'Install: libmpc3:amd64 (1.0.3-1+b2, automatic), '
        'manpages:amd64 (4.10-2, autom...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[4]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Install: containerd.io:amd64 (1.2.6-3), '
        'linux-headers-4.9.0-9-common:amd64 (4.9.168-1+deb9u3, automatic), '
        'aufs-tools:amd64 (1:4.1+20161219-1, automatic), '
        'aufs-dkms:amd64 (4.9+20161219-1, automatic), '
        'cgroupfs-mount:amd64 (1.3, automatic), '
        'linux-compiler-gcc-6-x86:amd64 (4.9.168-1+deb9u3, automatic), '
        'dkms:amd64 (2.3-2, automatic), libltdl7:amd64 (2.4.6-2, automatic), '
        'linux-headers-amd64:amd64 (4.9+80+deb9u7, automatic), '
        'linux-kbuild-4.9:amd64 (4.9.168-1+deb9u3, automatic), '
        'linux-headers-4.9.0-9-amd64:amd64 (4.9.168-1+deb9u3, automatic), '
        'pigz:amd64 (2.3.4-1, automatic), '
        'docker-ce:amd64 (5:18.09.7~3-0~debian-stretch), '
        'docker-ce-cli:amd64 (5:18.09.7~3-0~debian-stretch) '
        '[Commandline: apt-get install -y docker-ce docker-ce-cli containerd.io'
        '] [Error: Sub-process /usr/bin/dpkg returned an error code (1)]')
    expected_short_message = (
        'Install: containerd.io:amd64 (1.2.6-3), '
        'linux-headers-4.9.0-9-common:amd64 (4...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[6]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_message = (
        'Remove: volatility:amd64 (2.6-1), forensics-all:amd64 (1.5) '
        '[Commandline: apt-get remove volatility] '
        '[Requested-By: jxs (1005)]')
    expected_short_message = (
        'Remove: volatility:amd64 (2.6-1), forensics-all:amd64 (1.5)')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[9]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.CheckTimestamp(event.timestamp, '2019-07-12 04:19:26.000000')

    expected_message = (
        'Remove: python-distorm3:amd64 (3.3.4-2), '
        'python-imaging:amd64 (4.0.0-4), python-py:amd64 (1.4.32-3), '
        'python-openpyxl:amd64 (2.3.0-3), libdistorm3-3:amd64 (3.3.4-2), '
        'python-jdcal:amd64 (1.0-1.2~deb9u1) [Commandline: apt-get autoremove] '
        '[Requested-By: jxs (1005)]')
    expected_short_message = (
        'Remove: python-distorm3:amd64 (3.3.4-2), '
        'python-imaging:amd64 (4.0.0-4), pyth...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseInvalidLog(self):
    """Tests the Parse function on a non APT History log."""
    parser = apt_history.APTHistoryLogParser()
    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(['setupapi.dev.log'], parser)


if __name__ == '__main__':
  unittest.main()
