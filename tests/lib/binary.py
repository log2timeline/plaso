#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the binary library functions."""

from __future__ import unicode_literals

import unittest

from plaso.lib import binary

from tests import test_lib as shared_test_lib


class BinaryTests(shared_test_lib.BaseTestCase):
  """A unit test for the binary helper functions."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    # String: "þrándur" - uses surrogate pairs to test four byte character
    # decoding.
    self._unicode_string_1 = (
        b'\xff\xfe\xfe\x00\x72\x00\xe1\x00\x6E\x00\x64\x00\x75\x00\x72\x00')

    # String: "What\x00is".
    self._ascii_string_1 = (
        b'\x57\x00\x68\x00\x61\x00\x74\x00\x00\x00\x69\x00\x73\x00')

    # String: "What is this?".
    self._ascii_string_2 = (
        b'\x57\x00\x68\x00\x61\x00\x74\x00\x20\x00\x69\x00\x73\x00'
        b'\x20\x00\x74\x00\x68\x00\x69\x00\x73\x00\x3F\x00')

  @shared_test_lib.skipUnlessHasTestFile(['PING.EXE-B29F6629.pf'])
  def testReadUTF16Stream(self):
    """Test reading an UTF-16 stream from a file-like object."""
    test_file_path = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      # Read a null char terminated string.
      file_object.seek(0x10)
      self.assertEqual(binary.ReadUTF16Stream(file_object), 'PING.EXE')

      # Read a fixed size string.
      file_object.seek(0x27f8)
      expected_string = '\\DEVICE\\HARDDISKVOLUME'
      string = binary.ReadUTF16Stream(file_object, byte_size=44)
      self.assertEqual(string, expected_string)

      file_object.seek(0x27f8)
      expected_string = '\\DEVICE\\HARDDISKVOLUME1'
      string = binary.ReadUTF16Stream(file_object, byte_size=46)
      self.assertEqual(string, expected_string)

      # Read another null char terminated string.
      file_object.seek(7236)
      self.assertEqual(
          binary.ReadUTF16Stream(file_object),
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL')

  @shared_test_lib.skipUnlessHasTestFile(['PING.EXE-B29F6629.pf'])
  def testUTF16StreamCopyToString(self):
    """Test copying an UTF-16 byte stream to a string."""
    test_file_path = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      # Read a null char terminated string.
      self.assertEqual(
          binary.UTF16StreamCopyToString(byte_stream[0x10:]), 'PING.EXE')

      # Read a fixed size string.
      expected_string = '\\DEVICE\\HARDDISKVOLUME'
      string = binary.UTF16StreamCopyToString(
          byte_stream[0x27f8:], byte_stream_size=44)
      self.assertEqual(string, expected_string)

      expected_string = '\\DEVICE\\HARDDISKVOLUME1'
      string = binary.UTF16StreamCopyToString(
          byte_stream[0x27f8:], byte_stream_size=46)
      self.assertEqual(string, expected_string)

      # Read another null char terminated string.
      expected_string = (
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL')

      string = binary.UTF16StreamCopyToString(byte_stream[7236:])
      self.assertEqual(string, expected_string)

  @shared_test_lib.skipUnlessHasTestFile(['PING.EXE-B29F6629.pf'])
  def testArrayOfUTF16StreamCopyToString(self):
    """Test copying an array of UTF-16 byte streams to strings."""
    test_file_path = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      strings_array = binary.ArrayOfUTF16StreamCopyToString(
          byte_stream[0x1c44:], byte_stream_size=2876)
      expected_strings_array = [
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\APISETSCHEMA.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\PING.EXE',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SECHOST.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IPHLPAPI.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NSI.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINNSI.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LPK.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USP10.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WS2_32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IMM32.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSCTF.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\EN-US\\PING.EXE.MUI',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\GLOBALIZATION\\SORTING\\'
          'SORTDEFAULT.NLS',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSWSOCK.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHQOS.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHTCPIP.DLL',
          '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHIP6.DLL']

      self.assertEqual(strings_array, expected_strings_array)

  @shared_test_lib.skipUnlessHasTestFile(['PING.EXE-B29F6629.pf'])
  def testArrayOfUTF16StreamCopyToStringTable(self):
    """Test copying an array of UTF-16 byte streams to a string table."""
    test_file_path = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      string_table = binary.ArrayOfUTF16StreamCopyToStringTable(
          byte_stream[0x1c44:], byte_stream_size=2876)
      expected_string_table = {
          0: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
          102: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
          210: ('\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\'
                'APISETSCHEMA.DLL'),
          326: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL',
          438: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
          542: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\PING.EXE',
          642: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
          750: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
          854: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SECHOST.DLL',
          960: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
          1064: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IPHLPAPI.DLL',
          1172: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NSI.DLL',
          1270: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINNSI.DLL',
          1374: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
          1478: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
          1580: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LPK.DLL',
          1678: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USP10.DLL',
          1780: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WS2_32.DLL',
          1884: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IMM32.DLL',
          1986: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSCTF.DLL',
          2088: ('\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\EN-US\\'
                 'PING.EXE.MUI'),
          2208: ('\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\GLOBALIZATION\\'
                 'SORTING\\SORTDEFAULT.NLS'),
          2348: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSWSOCK.DLL',
          2454: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHQOS.DLL',
          2558: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHTCPIP.DLL',
          2666: '\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHIP6.DLL'}

      self.assertEqual(string_table, expected_string_table)

  def testReadUTF16(self):
    """Test reading a UTF-16 string."""
    self.assertEqual(binary.ReadUTF16(self._ascii_string_1), 'Whatis')

    self.assertEqual(binary.ReadUTF16(self._ascii_string_2), 'What is this?')

    unicode_text = binary.ReadUTF16(self._unicode_string_1)
    self.assertEqual(unicode_text, 'þrándur')

  def testHex(self):
    """Test the hexadecimal representation of data."""
    hex_string_1 = binary.HexifyBuffer(self._ascii_string_1)
    hex_compare = (
        '\\x57\\x00\\x68\\x00\\x61\\x00\\x74\\x00\\x00\\x00\\x69\\x00'
        '\\x73\\x00')
    self.assertEqual(hex_string_1, hex_compare)

    hex_string_2 = binary.HexifyBuffer(self._unicode_string_1)
    hex_compare_unicode = (
        '\\xff\\xfe\\xfe\\x00\\x72\\x00\\xe1\\x00\\x6e\\x00\\x64\\x00'
        '\\x75\\x00\\x72\\x00')

    self.assertEqual(hex_string_2, hex_compare_unicode)


if __name__ == '__main__':
  unittest.main()
