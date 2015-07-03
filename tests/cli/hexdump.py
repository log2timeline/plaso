#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the binary data as hexadecimal representation class."""

import unittest

from plaso.cli import hexdump


class HexdumpTest(unittest.TestCase):
  """Tests for the hexadecimal representation formatter (hexdump) class."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def testAddDataLocationOption(self):
    """Tests the AddDataLocationOption function."""
    expected_hexadecimal_string = u'\n'.join([
        u'0000000: 0001 0203 0405 0607 0809 0a0b 0c0d 0e0f  ................',
        u'0000010: 1011 1213 1415 1617 1819 1a1b 1c1d 1e1f  ................',
        u'0000020: 2021 2223 2425 2627 2829 2a2b 2c2d 2e2f   !"#$%&\'()*+,-./',
        u'0000030: 3031 3233 3435 3637 3839 3a3b 3c3d 3e3f  0123456789:;<=>?',
        u'0000040: 4041 4243 4445 4647 4849 4a4b 4c4d 4e4f  @ABCDEFGHIJKLMNO',
        u'0000050: 5051 5253 5455 5657 5859 5a5b 5c5d 5e5f  PQRSTUVWXYZ[\\]^_',
        u'0000060: 6061 6263 6465 6667 6869 6a6b 6c6d 6e6f  `abcdefghijklmno',
        u'0000070: 7071 7273 7475 7677 7879 7a7b 7c7d 7e7f  pqrstuvwxyz{|}~.',
        u'0000080: 8081 8283 8485 8687 8889 8a8b 8c8d 8e8f  ................',
        u'0000090: 9091 9293 9495 9697 9899 9a9b 9c9d 9e9f  ................',
        u'00000a0: a0a1 a2a3 a4a5 a6a7 a8a9 aaab acad aeaf  ................',
        u'00000b0: b0b1 b2b3 b4b5 b6b7 b8b9 babb bcbd bebf  ................',
        u'00000c0: c0c1 c2c3 c4c5 c6c7 c8c9 cacb cccd cecf  ................',
        u'00000d0: d0d1 d2d3 d4d5 d6d7 d8d9 dadb dcdd dedf  ................',
        u'00000e0: e0e1 e2e3 e4e5 e6e7 e8e9 eaeb eced eeef  ................',
        u'00000f0: f0f1 f2f3 f4f5 f6f7 f8f9 fafb fcfd feff  ................'])

    test_data = b''.join([chr(value) for value in range(256)])
    hexadecimal_string = hexdump.Hexdump.FormatData(test_data)
    self.assertEqual(hexadecimal_string, expected_hexadecimal_string)


if __name__ == '__main__':
  unittest.main()
