#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the binary library functions."""

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

  @shared_test_lib.skipUnlessHasTestFile([u'PING.EXE-B29F6629.pf'])
  def testReadUTF16Stream(self):
    """Test reading an UTF-16 stream from a file-like object."""
    test_file_path = self._GetTestFilePath([u'PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      # Read a null char terminated string.
      file_object.seek(0x10)
      self.assertEqual(binary.ReadUTF16Stream(file_object), u'PING.EXE')

      # Read a fixed size string.
      file_object.seek(0x27f8)
      expected_string = u'\\DEVICE\\HARDDISKVOLUME'
      string = binary.ReadUTF16Stream(file_object, byte_size=44)
      self.assertEqual(string, expected_string)

      file_object.seek(0x27f8)
      expected_string = u'\\DEVICE\\HARDDISKVOLUME1'
      string = binary.ReadUTF16Stream(file_object, byte_size=46)
      self.assertEqual(string, expected_string)

      # Read another null char terminated string.
      file_object.seek(7236)
      self.assertEqual(
          binary.ReadUTF16Stream(file_object),
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL')

  @shared_test_lib.skipUnlessHasTestFile([u'PING.EXE-B29F6629.pf'])
  def testUTF16StreamCopyToString(self):
    """Test copying an UTF-16 byte stream to a string."""
    test_file_path = self._GetTestFilePath([u'PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      # Read a null char terminated string.
      self.assertEqual(
          binary.UTF16StreamCopyToString(byte_stream[0x10:]), u'PING.EXE')

      # Read a fixed size string.
      expected_string = u'\\DEVICE\\HARDDISKVOLUME'
      string = binary.UTF16StreamCopyToString(
          byte_stream[0x27f8:], byte_stream_size=44)
      self.assertEqual(string, expected_string)

      expected_string = u'\\DEVICE\\HARDDISKVOLUME1'
      string = binary.UTF16StreamCopyToString(
          byte_stream[0x27f8:], byte_stream_size=46)
      self.assertEqual(string, expected_string)

      # Read another null char terminated string.
      expected_string = (
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL')

      string = binary.UTF16StreamCopyToString(byte_stream[7236:])
      self.assertEqual(string, expected_string)

  @shared_test_lib.skipUnlessHasTestFile([u'PING.EXE-B29F6629.pf'])
  def testArrayOfUTF16StreamCopyToString(self):
    """Test copying an array of UTF-16 byte streams to strings."""
    test_file_path = self._GetTestFilePath([u'PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      strings_array = binary.ArrayOfUTF16StreamCopyToString(
          byte_stream[0x1c44:], byte_stream_size=2876)
      expected_strings_array = [
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\APISETSCHEMA.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\PING.EXE',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SECHOST.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IPHLPAPI.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NSI.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINNSI.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LPK.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USP10.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WS2_32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IMM32.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSCTF.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\EN-US\\PING.EXE.MUI',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\GLOBALIZATION\\SORTING\\'
          u'SORTDEFAULT.NLS',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSWSOCK.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHQOS.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHTCPIP.DLL',
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHIP6.DLL']

      self.assertEqual(strings_array, expected_strings_array)

  @shared_test_lib.skipUnlessHasTestFile([u'PING.EXE-B29F6629.pf'])
  def testArrayOfUTF16StreamCopyToStringTable(self):
    """Test copying an array of UTF-16 byte streams to a string table."""
    test_file_path = self._GetTestFilePath([u'PING.EXE-B29F6629.pf'])

    with open(test_file_path, 'rb') as file_object:
      byte_stream = file_object.read()

      string_table = binary.ArrayOfUTF16StreamCopyToStringTable(
          byte_stream[0x1c44:], byte_stream_size=2876)
      expected_string_table = {
          0: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL',
          102: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNEL32.DLL',
          210: (u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\'
                u'APISETSCHEMA.DLL'),
          326: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\KERNELBASE.DLL',
          438: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS',
          542: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\PING.EXE',
          642: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\ADVAPI32.DLL',
          750: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSVCRT.DLL',
          854: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\SECHOST.DLL',
          960: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\RPCRT4.DLL',
          1064: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IPHLPAPI.DLL',
          1172: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NSI.DLL',
          1270: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WINNSI.DLL',
          1374: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USER32.DLL',
          1478: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\GDI32.DLL',
          1580: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LPK.DLL',
          1678: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\USP10.DLL',
          1780: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WS2_32.DLL',
          1884: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\IMM32.DLL',
          1986: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSCTF.DLL',
          2088: (u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\EN-US\\'
                 u'PING.EXE.MUI'),
          2208: (u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\GLOBALIZATION\\'
                 u'SORTING\\SORTDEFAULT.NLS'),
          2348: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\MSWSOCK.DLL',
          2454: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHQOS.DLL',
          2558: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHTCPIP.DLL',
          2666: u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\WSHIP6.DLL'}

      self.assertEqual(string_table, expected_string_table)

  def testStringParsing(self):
    """Test parsing the ASCII string."""
    self.assertEqual(binary.ReadUTF16(self._ascii_string_1), u'Whatis')

    self.assertEqual(binary.ReadUTF16(self._ascii_string_2), u'What is this?')

    uni_text = binary.ReadUTF16(self._unicode_string_1)
    self.assertEqual(uni_text, u'þrándur')

  def testHex(self):
    """Test the hexadecimal representation of data."""
    hex_string_1 = binary.HexifyBuffer(self._ascii_string_1)
    hex_compare = (
        b'\\x57\\x00\\x68\\x00\\x61\\x00\\x74\\x00\\x00\\x00\\x69\\x00'
        b'\\x73\\x00')
    self.assertEqual(hex_string_1, hex_compare)

    hex_string_2 = binary.HexifyBuffer(self._unicode_string_1)
    hex_compare_unicode = (
        b'\\xff\\xfe\\xfe\\x00\\x72\\x00\\xe1\\x00\\x6e\\x00\\x64\\x00'
        b'\\x75\\x00\\x72\\x00')

    self.assertEqual(hex_string_2, hex_compare_unicode)


if __name__ == '__main__':
  unittest.main()
