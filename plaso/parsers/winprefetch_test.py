#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Windows prefetch parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winprefetch as winprefetch_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import winprefetch


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = winprefetch.WinPrefetchParser(pre_obj)

  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    test_file = self._GetTestFilePath(['CMD.EXE-087B4001.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 2)

    # The prefetch last run event.
    event_object = event_objects[1]

    self.assertEquals(event_object.version, 17)
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-03-10 10:11:49.281250')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'CMD.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x087b4001)
    self.assertEquals(event_object.volume_serial_numbers[0], 0x24cb074b)

    expected_mapped_files = [
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\UNICODE.NLS',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SORTTBLS.NLS',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\CMD.EXE',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHIMENG.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\APPPATCH\\SYSMAIN.SDB',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\APPPATCH\\ACGENRAL.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINMM.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\OLE32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\OLEAUT32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSACM32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\VERSION.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHELL32.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHLWAPI.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USERENV.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\UXTHEME.DLL',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\CTYPE.NLS',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SORTKEY.NLS',
        (u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\WINSXS\\X86_MICROSOFT.WINDOWS.'
         u'COMMON-CONTROLS_6595B64144CCF1DF_6.0.2600.2180_X-WW_A84F1FF9\\'
         u'COMCTL32.DLL'),
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\WINDOWSSHELL.MANIFEST',
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\COMCTL32.DLL',
        (u'\\DEVICE\\HARDDISKVOLUME1\\D50FF1E628137B1A251B47AB9466\\UPDATE\\'
         u'UPDATE.EXE.MANIFEST'),
        u'\\DEVICE\\HARDDISKVOLUME1\\$MFT',
        (u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\IE7\\SPUNINST\\SPUNINST.EXE.'
         u'MANIFEST'),
        (u'\\DEVICE\\HARDDISKVOLUME1\\D50FF1E628137B1A251B47AB9466\\UPDATE\\'
         u'IERESETICONS.EXE'),
        u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\IE7\\SPUNINST\\IERESETICONS.EXE']

    self.assertEquals(event_object.mapped_files, expected_mapped_files)

    # The volume creation event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-03-10 10:19:46.234375')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_msg = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Serial number: 0x24CB074B '
        u'Origin: CMD.EXE-087B4001.pf')

    expected_msg_short = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Origin: CMD.EXE-087B4001.pf')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    test_file = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 2)

    # The prefetch last run event.
    event_object = event_objects[1]
    self.assertEquals(event_object.version, 23)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-04-06 19:00:55.932955')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)

    self.assertEquals(event_object.executable, u'PING.EXE')
    self.assertEquals(event_object.prefetch_hash, 0xb29f6629)
    self.assertEquals(
        event_object.path, u'\\WINDOWS\\SYSTEM32\\PING.EXE')
    self.assertEquals(event_object.run_count, 14)
    self.assertEquals(
        event_object.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial_numbers[0], 0xac036525)

    expected_msg = (
        u'Prefetch [PING.EXE] was executed - run count 14 path: '
        u'\\WINDOWS\\SYSTEM32\\PING.EXE '
        u'hash: 0xB29F6629 '
        u'volume: 1 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUME1]')

    expected_msg_short = u'PING.EXE was run 14 time(s)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # The volume creation event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2010-11-10 17:37:26.484375')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

  def testParse23MultiVolume(self):
    """Tests the Parse function on a mulit volume version 23 Prefetch file."""
    test_file = self._GetTestFilePath(['WUAUCLT.EXE-830BCC14.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 6)

    # The prefetch last run event.
    event_object = event_objects[5]
    self.assertEquals(event_object.version, 23)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-03-15 21:17:39.807996')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)

    self.assertEquals(event_object.executable, u'WUAUCLT.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x830bcc14)
    self.assertEquals(
        event_object.path, u'\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE')
    self.assertEquals(event_object.run_count, 25)
    self.assertEquals(
        event_object.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial_numbers[0], 0xac036525)

    expected_msg = (
        u'Prefetch [WUAUCLT.EXE] was executed - run count 25 path: '
        u'\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE '
        u'hash: 0x830BCC14 '
        u'volume: 1 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUME1], '
        u'volume: 2 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY2], '
        u'volume: 3 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY4], '
        u'volume: 4 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY7], '
        u'volume: 5 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY8]')

    expected_msg_short = u'WUAUCLT.EXE was run 25 time(s)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # The volume creation event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2010-11-10 17:37:26.484375')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_msg = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Serial number: 0xAC036525 '
        u'Origin: WUAUCLT.EXE-830BCC14.pf')

    expected_msg_short = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Origin: WUAUCLT.EXE-830BCC14.pf')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    test_file = self._GetTestFilePath(['TASKHOST.EXE-3AE259FC.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 5)

    # The prefetch last run event.
    event_object = event_objects[1]
    self.assertEquals(event_object.version, 26)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-04 15:40:09.037833')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'TASKHOST.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x3ae259fc)

    # The prefetch previous last run event.
    event_object = event_objects[2]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-04 15:28:09.010356')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc,
        u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME))

    expected_mapped_files = [
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTDLL.DLL '
         u'[MFT entry: 46299, sequence: 1]'),
        u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKHOST.EXE',
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL32.DLL '
         u'[MFT entry: 45747, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL '
         u'[MFT entry: 45734, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\LOCALE.NLS '
         u'[MFT entry: 45777, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSVCRT.DLL '
         u'[MFT entry: 46033, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCRT4.DLL '
         u'[MFT entry: 46668, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\COMBASE.DLL '
         u'[MFT entry: 44616, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLEAUT32.DLL '
         u'[MFT entry: 46309, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLE32.DLL '
         u'[MFT entry: 46348, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCSS.DLL '
         u'[MFT entry: 46654, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL.APPCORE.DLL '
         u'[MFT entry: 45698, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPTBASE.DLL '
         u'[MFT entry: 44560, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPTPRIMITIVES.DLL '
         u'[MFT entry: 44355, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\USER32.DLL '
         u'[MFT entry: 47130, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\GDI32.DLL '
         u'[MFT entry: 45344, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\EN-US\\'
         u'TASKHOST.EXE.MUI'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SECHOST.DLL '
         u'[MFT entry: 46699, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CLBCATQ.DLL '
         u'[MFT entry: 44511, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACENGN.DLL '
         u'[MFT entry: 46549, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTMARTA.DLL '
         u'[MFT entry: 46262, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WEVTAPI.DLL '
         u'[MFT entry: 47223, sequence: 1]'),
        u'\\DEVICE\\HARDDISKVOLUME2\\$MFT',
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SQMAPI.DLL '
         u'[MFT entry: 46832, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\AEPIC.DLL '
         u'[MFT entry: 43991, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WINTRUST.DLL '
         u'[MFT entry: 47372, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SLWGA.DLL '
         u'[MFT entry: 46762, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\DXGI.DLL '
         u'[MFT entry: 44935, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ESENT.DLL '
         u'[MFT entry: 45256, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WMICLNT.DLL '
         u'[MFT entry: 47413, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL '
         u'[MFT entry: 43994, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SFC_OS.DLL '
         u'[MFT entry: 46729, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\VERSION.DLL '
         u'[MFT entry: 47120, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPT32.DLL '
         u'[MFT entry: 44645, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSASN1.DLL '
         u'[MFT entry: 45909, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WTSAPI32.DLL '
         u'[MFT entry: 47527, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SPPC.DLL '
         u'[MFT entry: 46803, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\POWRPROF.DLL '
         u'[MFT entry: 46413, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\PROFAPI.DLL '
         u'[MFT entry: 46441, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         u'RACMETADATA.DAT [MFT entry: 39345, sequence: 2]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\GLOBALIZATION\\SORTING\\'
         u'SORTDEFAULT.NLS [MFT entry: 37452, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACRULES.XML '
         u'[MFT entry: 46509, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKSCHD.DLL '
         u'[MFT entry: 47043, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SSPICLI.DLL '
         u'[MFT entry: 46856, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\XMLLITE.DLL '
         u'[MFT entry: 47569, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         u'RACWMIEVENTDATA.DAT [MFT entry: 23870, sequence: 3]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         u'RACWMIDATABOOKMARKS.DAT [MFT entry: 23871, sequence: 2]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TPMTASKS.DLL '
         u'[MFT entry: 47003, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NCRYPT.DLL '
         u'[MFT entry: 46073, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPT.DLL '
         u'[MFT entry: 44346, sequence: 1]'),
        (u'\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTASN1.DLL '
         u'[MFT entry: 46261, sequence: 1]')]

    self.assertEquals(event_object.mapped_files, expected_mapped_files)

    # The volume creation event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-04 15:57:26.146547')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)


if __name__ == '__main__':
  unittest.main()
