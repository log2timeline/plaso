#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the regular expressions."""

import re
import unittest

from plaso.lib import regular_expressions

from tests import test_lib as shared_test_lib


class RegularExpressionsHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the regular expressions helper."""

  def testIPv4Address(self):
    """Tests the IPV4_ADDRESS expression."""
    text_regex = re.compile(regular_expressions.IPV4_ADDRESS)

    self.assertTrue(text_regex.match('1.2.3.4'))

    self.assertFalse(text_regex.match('1:2:3:4:5:6:7:8'))

  def testIPv6Address(self):
    """Tests the IPV6_ADDRESS expression."""
    text_regex = re.compile(regular_expressions.IPV6_ADDRESS)

    self.assertTrue(text_regex.match('1:2:3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('1::'))
    self.assertTrue(text_regex.match('1::8'))
    self.assertTrue(text_regex.match('1::7:8'))
    self.assertTrue(text_regex.match('1::6:7:8'))
    self.assertTrue(text_regex.match('1::5:6:7:8'))
    self.assertTrue(text_regex.match('1::4:5:6:7:8'))
    self.assertTrue(text_regex.match('1::3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('1:2::'))
    self.assertTrue(text_regex.match('1:2::8'))
    self.assertTrue(text_regex.match('1:2::7:8'))
    self.assertTrue(text_regex.match('1:2::6:7:8'))
    self.assertTrue(text_regex.match('1:2::5:6:7:8'))
    self.assertTrue(text_regex.match('1:2::4:5:6:7:8'))

    self.assertTrue(text_regex.match('1:2:3::'))
    self.assertTrue(text_regex.match('1:2:3::8'))
    self.assertTrue(text_regex.match('1:2:3::7:8'))
    self.assertTrue(text_regex.match('1:2:3::6:7:8'))
    self.assertTrue(text_regex.match('1:2:3::5:6:7:8'))

    self.assertTrue(text_regex.match('1:2:3:4::'))
    self.assertTrue(text_regex.match('1:2:3:4::8'))
    self.assertTrue(text_regex.match('1:2:3:4::7:8'))
    self.assertTrue(text_regex.match('1:2:3:4::6:7:8'))

    self.assertTrue(text_regex.match('1:2:3:4:5::'))
    self.assertTrue(text_regex.match('1:2:3:4:5::8'))
    self.assertTrue(text_regex.match('1:2:3:4:5::7:8'))

    self.assertTrue(text_regex.match('1:2:3:4:5:6::'))
    self.assertTrue(text_regex.match('1:2:3:4:5:6::8'))

    self.assertTrue(text_regex.match('1:2:3:4:5:6:7::'))

    self.assertTrue(text_regex.match('::8'))
    self.assertTrue(text_regex.match('::7:8'))
    self.assertTrue(text_regex.match('::6:7:8'))
    self.assertTrue(text_regex.match('::5:6:7:8'))
    self.assertTrue(text_regex.match('::4:5:6:7:8'))
    self.assertTrue(text_regex.match('::3:4:5:6:7:8'))
    self.assertTrue(text_regex.match('::2:3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('::'))

    self.assertTrue(text_regex.match('fe80::7:8%eth0'))
    self.assertTrue(text_regex.match('fe80::7:8%1'))

    self.assertTrue(text_regex.match('::255.255.255.255'))
    self.assertTrue(text_regex.match('::ffff:255.255.255.255'))
    self.assertTrue(text_regex.match('::ffff:0:255.255.255.255'))

    self.assertTrue(text_regex.match('2001:db8:3:4::192.0.2.33'))
    self.assertTrue(text_regex.match('64:ff9b::192.0.2.33'))

    self.assertFalse(text_regex.match('1.2.3.4'))

  def testIPAddress(self):
    """Tests the IP_ADDRESS expression."""
    text_regex = re.compile(regular_expressions.IP_ADDRESS)

    self.assertTrue(text_regex.match('1.2.3.4'))

    self.assertTrue(text_regex.match('1:2:3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('1::'))
    self.assertTrue(text_regex.match('1::8'))
    self.assertTrue(text_regex.match('1::7:8'))
    self.assertTrue(text_regex.match('1::6:7:8'))
    self.assertTrue(text_regex.match('1::5:6:7:8'))
    self.assertTrue(text_regex.match('1::4:5:6:7:8'))
    self.assertTrue(text_regex.match('1::3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('1:2::'))
    self.assertTrue(text_regex.match('1:2::8'))
    self.assertTrue(text_regex.match('1:2::7:8'))
    self.assertTrue(text_regex.match('1:2::6:7:8'))
    self.assertTrue(text_regex.match('1:2::5:6:7:8'))
    self.assertTrue(text_regex.match('1:2::4:5:6:7:8'))

    self.assertTrue(text_regex.match('1:2:3::'))
    self.assertTrue(text_regex.match('1:2:3::8'))
    self.assertTrue(text_regex.match('1:2:3::7:8'))
    self.assertTrue(text_regex.match('1:2:3::6:7:8'))
    self.assertTrue(text_regex.match('1:2:3::5:6:7:8'))

    self.assertTrue(text_regex.match('1:2:3:4::'))
    self.assertTrue(text_regex.match('1:2:3:4::8'))
    self.assertTrue(text_regex.match('1:2:3:4::7:8'))
    self.assertTrue(text_regex.match('1:2:3:4::6:7:8'))

    self.assertTrue(text_regex.match('1:2:3:4:5::'))
    self.assertTrue(text_regex.match('1:2:3:4:5::8'))
    self.assertTrue(text_regex.match('1:2:3:4:5::7:8'))

    self.assertTrue(text_regex.match('1:2:3:4:5:6::'))
    self.assertTrue(text_regex.match('1:2:3:4:5:6::8'))

    self.assertTrue(text_regex.match('1:2:3:4:5:6:7::'))

    self.assertTrue(text_regex.match('::8'))
    self.assertTrue(text_regex.match('::7:8'))
    self.assertTrue(text_regex.match('::6:7:8'))
    self.assertTrue(text_regex.match('::5:6:7:8'))
    self.assertTrue(text_regex.match('::4:5:6:7:8'))
    self.assertTrue(text_regex.match('::3:4:5:6:7:8'))
    self.assertTrue(text_regex.match('::2:3:4:5:6:7:8'))

    self.assertTrue(text_regex.match('::'))

    self.assertTrue(text_regex.match('fe80::7:8%eth0'))
    self.assertTrue(text_regex.match('fe80::7:8%1'))

    self.assertTrue(text_regex.match('::255.255.255.255'))
    self.assertTrue(text_regex.match('::ffff:255.255.255.255'))
    self.assertTrue(text_regex.match('::ffff:0:255.255.255.255'))

    self.assertTrue(text_regex.match('2001:db8:3:4::192.0.2.33'))
    self.assertTrue(text_regex.match('64:ff9b::192.0.2.33'))


if __name__ == '__main__':
  unittest.main()
