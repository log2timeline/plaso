#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows prefetch parser."""

import unittest

from plaso.parsers import winprefetch

from tests.parsers import test_lib


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['CMD.EXE-087B4001.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch last run event.
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

    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'CMD.EXE',
        'last_run_time': '2013-03-10T10:11:49.2812500+00:00',
        'mapped_files': expected_mapped_files,
        'prefetch_hash': 0x087b4001,
        'version': 17,
        'volume_serial_numbers': [0x24cb074b]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check the volume creation event.
    expected_event_values = {
        'creation_time': '2013-03-10T10:19:46.2343750+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\DEVICE\\HARDDISKVOLUME1',
        'origin': 'CMD.EXE-087B4001.pf',
        'serial_number': 0x24cb074b}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['PING.EXE-B29F6629.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'PING.EXE',
        'last_run_time': '2012-04-06T19:00:55.9329556+00:00',
        'path_hints': ['\\WINDOWS\\SYSTEM32\\PING.EXE'],
        'prefetch_hash': 0xb29f6629,
        'run_count': 14,
        'version': 23,
        'volume_device_paths': ['\\DEVICE\\HARDDISKVOLUME1'],
        'volume_serial_numbers': [0xac036525]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2010-11-10T17:37:26.4843750+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\DEVICE\\HARDDISKVOLUME1',
        'origin': 'PING.EXE-B29F6629.pf',
        'serial_number': 0xac036525}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse23MultiVolume(self):
    """Tests the Parse function on a multi volume version 23 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['WUAUCLT.EXE-830BCC14.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'WUAUCLT.EXE',
        'last_run_time': '2012-03-15T21:17:39.8079963+00:00',
        'path_hints': ['\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE'],
        'prefetch_hash': 0x830bcc14,
        'run_count': 25,
        'version': 23,
        'volume_device_paths': [
            '\\DEVICE\\HARDDISKVOLUME1',
            '\\DEVICE\\HARDDISKVOLUMESHADOWCOPY2',
            '\\DEVICE\\HARDDISKVOLUMESHADOWCOPY4',
            '\\DEVICE\\HARDDISKVOLUMESHADOWCOPY7',
            '\\DEVICE\\HARDDISKVOLUMESHADOWCOPY8'],
        'volume_serial_numbers': [
            0xac036525, 0xac036525, 0xac036525, 0xac036525, 0xac036525]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2010-11-10T17:37:26.4843750+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\DEVICE\\HARDDISKVOLUME1',
        'origin': 'WUAUCLT.EXE-830BCC14.pf',
        'serial_number': 0xac036525}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['TASKHOST.EXE-3AE259FC.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_mapped_files = [
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTDLL.DLL [46299-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKHOST.EXE',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL32.DLL [45747-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL '
         '[45734-1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\LOCALE.NLS [45777-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSVCRT.DLL [46033-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCRT4.DLL [46668-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\COMBASE.DLL [44616-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLEAUT32.DLL [46309-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\OLE32.DLL [46348-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RPCSS.DLL [46654-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\KERNEL.APPCORE.DLL '
         '[45698-1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPTBASE.DLL [44560-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPTPRIMITIVES.DLL '
         '[44355-1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\USER32.DLL [47130-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\GDI32.DLL [45344-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\EN-US\\'
         'TASKHOST.EXE.MUI'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SECHOST.DLL [46699-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CLBCATQ.DLL [44511-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACENGN.DLL [46549-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTMARTA.DLL [46262-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WEVTAPI.DLL [47223-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\$MFT',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SQMAPI.DLL [46832-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\AEPIC.DLL [43991-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WINTRUST.DLL [47372-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SLWGA.DLL [46762-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\DXGI.DLL [44935-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ESENT.DLL [45256-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WMICLNT.DLL [47413-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL [43994-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SFC_OS.DLL [46729-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\VERSION.DLL [47120-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\CRYPT32.DLL [44645-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\MSASN1.DLL [45909-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\WTSAPI32.DLL [47527-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SPPC.DLL [46803-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\POWRPROF.DLL [46413-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\PROFAPI.DLL [46441-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACMETADATA.DAT [39345-2]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\GLOBALIZATION\\SORTING\\'
         'SORTDEFAULT.NLS [37452-1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\RACRULES.XML [46509-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TASKSCHD.DLL [47043-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\SSPICLI.DLL [46856-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\XMLLITE.DLL [47569-1]',
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACWMIEVENTDATA.DAT [23870-3]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\PROGRAMDATA\\MICROSOFT\\RAC\\STATEDATA\\'
         'RACWMIDATABOOKMARKS.DAT [23871-2]'),
        ('\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\TPMTASKS.DLL '
         '[47003-1]'),
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NCRYPT.DLL [46073-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\BCRYPT.DLL [44346-1]',
        '\\DEVICE\\HARDDISKVOLUME2\\WINDOWS\\SYSTEM32\\NTASN1.DLL [46261-1]']

    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'TASKHOST.EXE',
        'last_run_time': '2013-10-04T15:40:09.0378333+00:00',
        'mapped_files': expected_mapped_files,
        'prefetch_hash': 0x3ae259fc,
        'previous_run_times': [
            '2013-10-04T15:28:09.0103565+00:00',
            '2013-10-04T06:19:54.5960606+00:00',
            '2013-10-04T06:11:13.6429375+00:00'],
        'run_count': 4,
        'version': 26}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2013-10-04T15:57:26.1465476+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\DEVICE\\HARDDISKVOLUME2',
        'origin': 'TASKHOST.EXE-3AE259FC.pf',
        'serial_number': 0x686c4249}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse30Compressed(self):
    """Tests the Parse function on a compressed version 30 Prefetch file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(
        ['BYTECODEGENERATOR.EXE-C1E9BCE6.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'BYTECODEGENERATOR.EXE',
        'last_run_time': '2015-05-14T22:11:58.0911341+00:00',
        'prefetch_hash': 0xc1e9bce6,
        'previous_run_times': [
            '2015-05-14T22:11:55.3576520+00:00',
            '2015-05-14T22:11:45.5135991+00:00',
            '2015-05-14T22:11:25.8427278+00:00',
            '2015-05-14T22:11:19.8586549+00:00',
            '2015-05-14T22:11:05.9066547+00:00',
            '2015-05-14T22:10:38.2515193+00:00'],
        'run_count': 7,
        'version': 30}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    self.assertEqual(len(event_data.mapped_files), 1085)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2015-05-15T06:54:55.1392941+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\VOLUME{01d08edc0cbccaad-3e0d2d25}',
        'origin': 'BYTECODEGENERATOR.EXE-C1E9BCE6.pf',
        'serial_number': 0x3e0d2d25}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse30Variant1Compressed(self):
    """Tests the Parse function on a compressed version 30 variant 1 file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['ONEDRIVE.EXE-7E152375.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'ONEDRIVE.EXE',
        'last_run_time': '2015-05-14T22:11:05.4852771+00:00',
        'prefetch_hash': 0x7e152375,
        'previous_run_times': [
            '2015-05-14T22:10:28.6747101+00:00'],
        'run_count': 2,
        'version': 30}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    self.assertEqual(len(event_data.mapped_files), 134)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2015-05-15T06:54:55.1392941+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\VOLUME{01d08edc0cbccaad-3e0d2d25}',
        'origin': 'ONEDRIVE.EXE-7E152375.pf',
        'serial_number': 0x3e0d2d25}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParse30Variant2Compressed(self):
    """Tests the Parse function on a compressed version 30 variant 2 file."""
    parser = winprefetch.WinPrefetchParser()
    storage_writer = self._ParseFile(['NOTEPAD.EXE-D8414F97.pf'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the prefetch execution event data.
    expected_event_values = {
        'data_type': 'windows:prefetch:execution',
        'executable': 'NOTEPAD.EXE',
        'last_run_time': '2019-06-05T19:55:04.8777787+00:00',
        'prefetch_hash': 0xd8414f97,
        'previous_run_times': [
            '2019-06-05T19:23:00.8157052+00:00'],
        'run_count': 2,
        'version': 30}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    self.assertEqual(len(event_data.mapped_files), 56)

    # Check the volume creation event data.
    expected_event_values = {
        'creation_time': '2017-07-30T19:40:03.5487843+00:00',
        'data_type': 'windows:volume:creation',
        'device_path': '\\VOLUME{01d3096ba3a46863-2ca3d1ae}',
        'origin': 'NOTEPAD.EXE-D8414F97.pf',
        'serial_number': 0x2ca3d1ae}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
