#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows prefetch parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winprefetch as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import winprefetch

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  @shared_test_lib.skipUnlessHasTestFile(['CMD.EXE-087B4001.pf'])
  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['CMD.EXE-087B4001.pf'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, 'windows:prefetch:execution')
    self.assertEqual(event.version, 17)

    self.CheckTimestamp(event.timestamp, '2013-03-10 10:11:49.281250')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, 'CMD.EXE')
    self.assertEqual(event.prefetch_hash, 0x087b4001)
    self.assertEqual(event.volume_serial_numbers[0], 0x24cb074b)

    expected_mapped_files = [
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\UNICODE.NLS',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SORTTBLS.NLS',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\CMD.EXE',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHIMENG.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\APPPATCH\\SYSMAIN.SDB',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\APPPATCH\\ACGENRAL.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINMM.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\OLE32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\OLEAUT32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSACM32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\VERSION.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHELL32.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SHLWAPI.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USERENV.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\UXTHEME.DLL',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\CTYPE.NLS',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SORTKEY.NLS',
        ('\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\WINSXS\\X86_MICROSOFT.WINDOWS.'
         'COMMON-CONTROLS_6595B64144CCF1DF_6.0.2600.2180_X-WW_A84F1FF9\\'
         'COMCTL32.DLL'),
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\WINDOWSSHELL.MANIFEST',
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\COMCTL32.DLL',
        ('\\DEVICE\\HARDDISKVOLUME1\\D50FF1E628137B1A251B47AB9466\\UPDATE\\'
         'UPDATE.EXE.MANIFEST'),
        '\\DEVICE\\HARDDISKVOLUME1\\$MFT',
        ('\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\IE7\\SPUNINST\\SPUNINST.EXE.'
         'MANIFEST'),
        ('\\DEVICE\\HARDDISKVOLUME1\\D50FF1E628137B1A251B47AB9466\\UPDATE\\'
         'IERESETICONS.EXE'),
        '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\IE7\\SPUNINST\\IERESETICONS.EXE']

    self.assertEqual(event.mapped_files, expected_mapped_files)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:volume:creation')

    self.CheckTimestamp(event.timestamp, '2013-03-10 10:19:46.234375')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        '\\DEVICE\\HARDDISKVOLUME1 '
        'Serial number: 0x24CB074B '
        'Origin: CMD.EXE-087B4001.pf')

    expected_short_message = (
        '\\DEVICE\\HARDDISKVOLUME1 '
        'Origin: CMD.EXE-087B4001.pf')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['PING.EXE-B29F6629.pf'])
  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['PING.EXE-B29F6629.pf'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, 'windows:prefetch:execution')
    self.assertEqual(event.version, 23)

    self.CheckTimestamp(event.timestamp, '2012-04-06 19:00:55.932956')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, 'PING.EXE')
    self.assertEqual(event.prefetch_hash, 0xb29f6629)
    self.assertEqual(event.path, '\\WINDOWS\\SYSTEM32\\PING.EXE')
    self.assertEqual(event.run_count, 14)
    self.assertEqual(event.volume_device_paths[0], '\\DEVICE\\HARDDISKVOLUME1')
    self.assertEqual(event.volume_serial_numbers[0], 0xac036525)

    expected_message = (
        'Prefetch [PING.EXE] was executed - run count 14 path: '
        '\\WINDOWS\\SYSTEM32\\PING.EXE '
        'hash: 0xB29F6629 '
        'volume: 1 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUME1]')

    expected_short_message = 'PING.EXE was run 14 time(s)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:volume:creation')

    self.CheckTimestamp(event.timestamp, '2010-11-10 17:37:26.484375')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

  @shared_test_lib.skipUnlessHasTestFile(['WUAUCLT.EXE-830BCC14.pf'])
  def testParse23MultiVolume(self):
    """Tests the Parse function on a multi volume version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['WUAUCLT.EXE-830BCC14.pf'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[5]

    self.assertEqual(event.data_type, 'windows:prefetch:execution')
    self.assertEqual(event.version, 23)

    self.CheckTimestamp(event.timestamp, '2012-03-15 21:17:39.807996')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, 'WUAUCLT.EXE')
    self.assertEqual(event.prefetch_hash, 0x830bcc14)
    self.assertEqual(event.path, '\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE')
    self.assertEqual(event.run_count, 25)
    self.assertEqual(event.volume_device_paths[0], '\\DEVICE\\HARDDISKVOLUME1')
    self.assertEqual(event.volume_serial_numbers[0], 0xac036525)

    expected_message = (
        'Prefetch [WUAUCLT.EXE] was executed - run count 25 path: '
        '\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE '
        'hash: 0x830BCC14 '
        'volume: 1 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUME1], '
        'volume: 2 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY2], '
        'volume: 3 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY4], '
        'volume: 4 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY7], '
        'volume: 5 [serial number: 0xAC036525, '
        'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY8]')

    expected_short_message = 'WUAUCLT.EXE was run 25 time(s)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:volume:creation')

    self.CheckTimestamp(event.timestamp, '2010-11-10 17:37:26.484375')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        '\\DEVICE\\HARDDISKVOLUME1 '
        'Serial number: 0xAC036525 '
        'Origin: WUAUCLT.EXE-830BCC14.pf')

    expected_short_message = (
        '\\DEVICE\\HARDDISKVOLUME1 '
        'Origin: WUAUCLT.EXE-830BCC14.pf')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['TASKHOST.EXE-3AE259FC.pf'])
  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['TASKHOST.EXE-3AE259FC.pf'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, 'windows:prefetch:execution')
    self.assertEqual(event.version, 26)

    self.CheckTimestamp(event.timestamp, '2013-10-04 15:40:09.037833')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, 'TASKHOST.EXE')
    self.assertEqual(event.prefetch_hash, 0x3ae259fc)

    # The prefetch previous last run event.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-10-04 15:28:09.010357')

    expected_timestamp_desc = 'Previous {0:s}'.format(
        definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.timestamp_desc, expected_timestamp_desc)

    expected_mapped_files = [
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTDLL.DLL '
         '[MFT entry: 46299, sequence: 1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKHOST.EXE',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL32.DLL '
         '[MFT entry: 45747, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL '
         '[MFT entry: 45734, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\LOCALE.NLS '
         '[MFT entry: 45777, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSVCRT.DLL '
         '[MFT entry: 46033, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCRT4.DLL '
         '[MFT entry: 46668, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\COMBASE.DLL '
         '[MFT entry: 44616, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLEAUT32.DLL '
         '[MFT entry: 46309, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLE32.DLL '
         '[MFT entry: 46348, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCSS.DLL '
         '[MFT entry: 46654, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL.APPCORE.DLL '
         '[MFT entry: 45698, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPTBASE.DLL '
         '[MFT entry: 44560, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPTPRIMITIVES.DLL '
         '[MFT entry: 44355, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\USER32.DLL '
         '[MFT entry: 47130, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\GDI32.DLL '
         '[MFT entry: 45344, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\EN-US\\'
         'TASKHOST.EXE.MUI'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SECHOST.DLL '
         '[MFT entry: 46699, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CLBCATQ.DLL '
         '[MFT entry: 44511, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACENGN.DLL '
         '[MFT entry: 46549, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTMARTA.DLL '
         '[MFT entry: 46262, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WEVTAPI.DLL '
         '[MFT entry: 47223, sequence: 1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\$MFT',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SQMAPI.DLL '
         '[MFT entry: 46832, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\AEPIC.DLL '
         '[MFT entry: 43991, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WINTRUST.DLL '
         '[MFT entry: 47372, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SLWGA.DLL '
         '[MFT entry: 46762, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\DXGI.DLL '
         '[MFT entry: 44935, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ESENT.DLL '
         '[MFT entry: 45256, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WMICLNT.DLL '
         '[MFT entry: 47413, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL '
         '[MFT entry: 43994, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SFC_OS.DLL '
         '[MFT entry: 46729, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\VERSION.DLL '
         '[MFT entry: 47120, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPT32.DLL '
         '[MFT entry: 44645, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSASN1.DLL '
         '[MFT entry: 45909, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WTSAPI32.DLL '
         '[MFT entry: 47527, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SPPC.DLL '
         '[MFT entry: 46803, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\POWRPROF.DLL '
         '[MFT entry: 46413, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\PROFAPI.DLL '
         '[MFT entry: 46441, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACMETADATA.DAT [MFT entry: 39345, sequence: 2]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\GLOBALIZATION\\SORTING\\'
         'SORTDEFAULT.NLS [MFT entry: 37452, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACRULES.XML '
         '[MFT entry: 46509, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKSCHD.DLL '
         '[MFT entry: 47043, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SSPICLI.DLL '
         '[MFT entry: 46856, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\XMLLITE.DLL '
         '[MFT entry: 47569, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACWMIEVENTDATA.DAT [MFT entry: 23870, sequence: 3]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACWMIDATABOOKMARKS.DAT [MFT entry: 23871, sequence: 2]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TPMTASKS.DLL '
         '[MFT entry: 47003, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NCRYPT.DLL '
         '[MFT entry: 46073, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPT.DLL '
         '[MFT entry: 44346, sequence: 1]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTASN1.DLL '
         '[MFT entry: 46261, sequence: 1]')]

    self.assertEqual(event.mapped_files, expected_mapped_files)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:volume:creation')

    self.CheckTimestamp(event.timestamp, '2013-10-04 15:57:26.146548')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

  @shared_test_lib.skipUnlessHasTestFile(['BYTECODEGENERATOR.EXE-C1E9BCE6.pf'])
  def testParse30Compressed(self):
    """Tests the Parse function on a compressed version 30 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['BYTECODEGENERATOR.EXE-C1E9BCE6.pf'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, 'windows:prefetch:execution')
    self.assertEqual(event.version, 30)

    self.assertEqual(event.data_type, 'windows:prefetch:execution')

    self.CheckTimestamp(event.timestamp, '2015-05-14 22:11:58.091134')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.executable, 'BYTECODEGENERATOR.EXE')
    self.assertEqual(event.prefetch_hash, 0xc1e9bce6)

    # The prefetch previous last run event.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2015-05-14 22:11:55.357652')
    expected_timestamp_desc = 'Previous {0:s}'.format(
        definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.timestamp_desc, expected_timestamp_desc)

    self.assertEqual(len(event.mapped_files), 1085)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:volume:creation')

    self.CheckTimestamp(event.timestamp, '2015-05-15 06:54:55.139294')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)


if __name__ == '__main__':
  unittest.main()
