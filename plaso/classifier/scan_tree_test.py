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
"""This file contains tests for the scan tree classes."""

import unittest

from plaso.classifier import patterns
from plaso.classifier import scan_tree
from plaso.classifier import specification


class ScanTreeNodeTest(unittest.TestCase):
  """Class to test the scan tree node."""

  def testAddByteValueWithPattern(self):
    """Function to test the add byte value with pattern function."""
    scan_node = scan_tree.ScanTreeNode(0)

    format_regf = specification.Specification('REGF')
    format_regf.AddNewSignature('regf', offset=0)

    format_esedb = specification.Specification('ESEDB')
    format_esedb.AddNewSignature('\xef\xcd\xab\x89', offset=4)

    signature_esedb = specification.Signature('\xef\xcd\xab\x89', offset=4)
    signature_regf = specification.Signature('regf', offset=0)

    pattern_regf = patterns.Pattern(0, signature_regf, format_regf)
    pattern_esedb = patterns.Pattern(0, signature_esedb, format_esedb)

    scan_node.AddByteValue('r', pattern_regf)
    scan_node.AddByteValue('\xef', pattern_esedb)

    self.assertRaises(
        ValueError, scan_node.AddByteValue, 'r', pattern_regf)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, -1, pattern_regf)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, 256, pattern_regf)

  def testAddByteValueWithScanNode(self):
    """Function to test the add byte value with scan node function."""
    scan_node = scan_tree.ScanTreeNode(0)
    scan_sub_node_0x41 = scan_tree.ScanTreeNode(1)
    scan_sub_node_0x80 = scan_tree.ScanTreeNode(1)

    scan_node.AddByteValue(0x41, scan_sub_node_0x41)
    scan_node.AddByteValue(0x80, scan_sub_node_0x80)

    self.assertRaises(
        ValueError, scan_node.AddByteValue, 0x80, scan_sub_node_0x80)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, -1, scan_sub_node_0x80)
    self.assertRaises(
        ValueError, scan_node.AddByteValue, 256, scan_sub_node_0x80)


if __name__ == '__main__':
  unittest.main()
