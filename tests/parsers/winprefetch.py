#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows prefetch parser."""

import unittest

from plaso.formatters import winprefetch  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winprefetch

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'CMD.EXE-087B4001.pf'])
  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile([u'CMD.EXE-087B4001.pf'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, u'windows:prefetch:execution')
    self.assertEqual(event.version, 17)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-10 10:11:49.281250')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.executable, u'CMD.EXE')
    self.assertEqual(event.prefetch_hash, 0x087b4001)
    self.assertEqual(event.volume_serial_numbers[0], 0x24cb074b)

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

    self.assertEqual(event.mapped_files, expected_mapped_files)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, u'windows:volume:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-10 10:19:46.234375')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Serial number: 0x24CB074B '
        u'Origin: CMD.EXE-087B4001.pf')

    expected_short_message = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Origin: CMD.EXE-087B4001.pf')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'PING.EXE-B29F6629.pf'])
  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile([u'PING.EXE-B29F6629.pf'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, u'windows:prefetch:execution')
    self.assertEqual(event.version, 23)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-06 19:00:55.932955')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, u'PING.EXE')
    self.assertEqual(event.prefetch_hash, 0xb29f6629)
    self.assertEqual(event.path, u'\\WINDOWS\\SYSTEM32\\PING.EXE')
    self.assertEqual(event.run_count, 14)
    self.assertEqual(event.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEqual(event.volume_serial_numbers[0], 0xac036525)

    expected_message = (
        u'Prefetch [PING.EXE] was executed - run count 14 path: '
        u'\\WINDOWS\\SYSTEM32\\PING.EXE '
        u'hash: 0xB29F6629 '
        u'volume: 1 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUME1]')

    expected_short_message = u'PING.EXE was run 14 time(s)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, u'windows:volume:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 17:37:26.484375')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

  @shared_test_lib.skipUnlessHasTestFile([u'WUAUCLT.EXE-830BCC14.pf'])
  def testParse23MultiVolume(self):
    """Tests the Parse function on a multi volume version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        [u'WUAUCLT.EXE-830BCC14.pf'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[5]

    self.assertEqual(event.data_type, u'windows:prefetch:execution')
    self.assertEqual(event.version, 23)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-15 21:17:39.807996')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    self.assertEqual(event.executable, u'WUAUCLT.EXE')
    self.assertEqual(event.prefetch_hash, 0x830bcc14)
    self.assertEqual(event.path, u'\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE')
    self.assertEqual(event.run_count, 25)
    self.assertEqual(event.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEqual(event.volume_serial_numbers[0], 0xac036525)

    expected_message = (
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

    expected_short_message = u'WUAUCLT.EXE was run 25 time(s)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, u'windows:volume:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 17:37:26.484375')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Serial number: 0xAC036525 '
        u'Origin: WUAUCLT.EXE-830BCC14.pf')

    expected_short_message = (
        u'\\DEVICE\\HARDDISKVOLUME1 '
        u'Origin: WUAUCLT.EXE-830BCC14.pf')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'TASKHOST.EXE-3AE259FC.pf'])
  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        [u'TASKHOST.EXE-3AE259FC.pf'], parser)

    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, u'windows:prefetch:execution')
    self.assertEqual(event.version, 26)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-04 15:40:09.037833')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.executable, u'TASKHOST.EXE')
    self.assertEqual(event.prefetch_hash, 0x3ae259fc)

    # The prefetch previous last run event.
    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-04 15:28:09.010356')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc,
        u'Previous {0:s}'.format(definitions.TIME_DESCRIPTION_LAST_RUN))

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

    self.assertEqual(event.mapped_files, expected_mapped_files)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, u'windows:volume:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-04 15:57:26.146547')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

  @shared_test_lib.skipUnlessHasTestFile([u'BYTECODEGENERATOR.EXE-C1E9BCE6.pf'])
  def testParse30Compressed(self):
    """Tests the Parse function on a compressed version 30 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        [u'BYTECODEGENERATOR.EXE-C1E9BCE6.pf'], parser)

    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    # The prefetch last run event.
    event = events[1]

    self.assertEqual(event.data_type, u'windows:prefetch:execution')
    self.assertEqual(event.version, 30)

    self.assertEqual(event.data_type, u'windows:prefetch:execution')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-05-14 22:11:58.091134')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)
    self.assertEqual(event.executable, u'BYTECODEGENERATOR.EXE')
    self.assertEqual(event.prefetch_hash, 0xc1e9bce6)

    # The prefetch previous last run event.
    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-05-14 22:11:55.357652')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc,
        u'Previous {0:s}'.format(definitions.TIME_DESCRIPTION_LAST_RUN))

    self.assertEqual(len(event.mapped_files), 1085)

    # The volume creation event.
    event = events[0]

    self.assertEqual(event.data_type, u'windows:volume:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-05-15 06:54:55.139294')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)


if __name__ == u'__main__':
  unittest.main()
