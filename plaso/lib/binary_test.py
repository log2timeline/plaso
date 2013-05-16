#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a unit test for the binary helper in Plaso."""
import os
import unittest

from plaso.lib import binary


class BinaryTests(unittest.TestCase):
  """A unit test for the binary helper functions."""

  def setUp(self):
    """Set up the needed variables used througout."""
    # String: "þrándur" - uses surrogate pairs to test four byte character
    # decoding.
    self._unicode_string_1 = (
        '\xff\xfe\xfe\x00\x72\x00\xe1\x00\x6E\x00\x64\x00\x75\x00\x72\x00')

    # String: "What\x00is".
    self._ascii_string_1 = (
        '\x57\x00\x68\x00\x61\x00\x74\x00\x00\x00\x69\x00\x73\x00')

    # String: "What is this?".
    self._ascii_string_2 = (
        '\x57\x00\x68\x00\x61\x00\x74\x00\x20\x00\x69\x00\x73\x00'
        '\x20\x00\x74\x00\x68\x00\x69\x00\x73\x00\x3F\x00')

  def testFile(self):
    """Test reading from a file."""
    path = os.path.join('test_data', 'ping.pf')
    with open(path, 'rb') as fh:
      fh.seek(0x10)
      # Read a null char terminated string.
      self.assertEquals(binary.ReadUtf16Stream(fh), 'PING.EXE')

      fh.seek(0x27F8)
      # Read a fixed size string.
      volume_string = binary.ReadUtf16Stream(fh, byte_size=46)
      self.assertEquals(volume_string, u'\\DEVICE\\HARDDISKVOLUME')
      fh.seek(7236)
      # Read another null char terminated string.
      self.assertEquals(
          binary.ReadUtf16Stream(fh),
          u'\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\NTDLL.DLL')

  def testStringParsing(self):
    """Test parsing the ASCII string."""
    self.assertEquals(binary.ReadUtf16(self._ascii_string_1), 'Whatis')

    self.assertEquals(binary.ReadUtf16(self._ascii_string_2), 'What is this?')

    uni_text = binary.ReadUtf16(self._unicode_string_1)
    self.assertEquals(uni_text, u'þrándur')

  def testHex(self):
    """Test the hexadecimal representation of data."""
    hex_string_1 = binary.HexifyBuffer(self._ascii_string_1)
    hex_compare = (
        '\\x57\\x00\\x68\\x00\\x61\\x00\\x74\\x00\\x00\\x00\\x69\\x00'
        '\\x73\\x00')
    self.assertEquals(hex_string_1, hex_compare)

    hex_string_2 = binary.HexifyBuffer(self._unicode_string_1)
    hex_compare_unicode = (
        '\\xff\\xfe\\xfe\\x00\\x72\\x00\\xe1\\x00\\x6e\\x00\\x64\\x00'
        '\\x75\\x00\\x72\\x00')

    self.assertEquals(hex_string_2, hex_compare_unicode)


if __name__ == '__main__':
  unittest.main()
