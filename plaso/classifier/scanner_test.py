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
"""This file contains tests for the format scanner classes."""
import unittest


from plaso.classifier import scanner
from plaso.classifier import specification
from plaso.classifier import test_store


class ScanNodeTest(unittest.TestCase):
  """Class to test ScanNode."""

  def testAddByteValueWithPattern(self):
    """Function to test the AddByteValue with Pattern function."""
    scan_node = scanner._ScanTreeNode(0)

    format_regf = specification.Specification("REGF")
    format_regf.AddSignature("regf", offset=0)

    format_esedb = specification.Specification("ESEDB")
    format_esedb.AddSignature("\xef\xcd\xab\x89", offset=4)

    signature_esedb = specification._Signature("\xef\xcd\xab\x89", offset=4)
    signature_regf = specification._Signature("regf", offset=0)

    pattern_regf = scanner.Pattern(0, signature_regf, format_regf)
    pattern_esedb = scanner.Pattern(0, signature_esedb, format_esedb)

    scan_node.AddByteValue("r", pattern_regf)
    scan_node.AddByteValue("\xef", pattern_esedb)

    self.assertRaises(
        ValueError, scan_node.AddByteValue, "r", pattern_regf)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, -1, pattern_regf)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, 256, pattern_regf)

  def testAddByteValueWithScanNode(self):
    """Function to test the AddByteValue with _ScanTreeNode function."""
    scan_node = scanner._ScanTreeNode(0)
    scan_sub_node_0x41 = scanner._ScanTreeNode(1)
    scan_sub_node_0x80 = scanner._ScanTreeNode(1)

    scan_node.AddByteValue(0x41, scan_sub_node_0x41)
    scan_node.AddByteValue(0x80, scan_sub_node_0x80)

    self.assertRaises(
        ValueError, scan_node.AddByteValue, 0x80, scan_sub_node_0x80)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, -1, scan_sub_node_0x80)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, 256, scan_sub_node_0x80)


class ScannerTest(unittest.TestCase):
  """Class to test Scanner."""

  def testInitialize(self):
    """Function to test the Initialize function."""
    store = test_store.CreateSpecificationStore()

    # Signature for LNK
    data1 = ("\x4c\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00"
             "\x00\x00\x00\x46")

    # Signature for REGF
    data2 = "regf"

    # Random data
    data3 = "\x01\xfa\xe0\xbe\x99\x8e\xdb\x70\xea\xcc\x6b\xae\x2f\xf5\xa2\xe4"

    # Boundary scan test
    data4a = ("\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00PK")
    data4b = ("\x07\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Z")

    # Large buffer test
    data5_size = 1024 * 1024
    data5 = "\x00" * (data5_size - 4)
    data5 += "PK\x07\x08"

    test_scanner = scanner.Scanner(store)

    scan_state = test_scanner.ScanStart()
    test_scanner.ScanBuffer(scan_state, 0, data1)
    test_scanner.ScanStop(scan_state)

    self.assertEqual(len(scan_state.GetResults()), 1)

    scan_state = test_scanner.ScanStart()
    test_scanner.ScanBuffer(scan_state, 0, data2)
    test_scanner.ScanStop(scan_state)

    self.assertEqual(len(scan_state.GetResults()), 1)

    scan_state = test_scanner.ScanStart()
    test_scanner.ScanBuffer(scan_state, 0, data3)
    test_scanner.ScanStop(scan_state)

    self.assertEqual(len(scan_state.GetResults()), 0)

    scan_state = test_scanner.ScanStart()
    test_scanner.ScanBuffer(scan_state, 0, data4a)
    test_scanner.ScanBuffer(scan_state, len(data4a), data4b)
    test_scanner.ScanStop(scan_state)

    self.assertEqual(len(scan_state.GetResults()), 1)

    scan_state = test_scanner.ScanStart()
    test_scanner.ScanBuffer(scan_state, 0, data5)
    test_scanner.ScanStop(scan_state)

    self.assertEqual(len(scan_state.GetResults()), 1)


if __name__ == "__main__":
  unittest.main()
