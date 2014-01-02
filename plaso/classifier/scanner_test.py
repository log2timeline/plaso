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
"""This file contains tests for the format scanner classes."""

import unittest

from plaso.classifier import scanner
from plaso.classifier import test_lib


class ScannerTest(unittest.TestCase):
  """Class to test the scanner."""

  def testInitialize(self):
    """Function to test the initialize function."""
    store = test_lib.CreateSpecificationStore()

    # Signature for LNK
    data1 = ('\x4c\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00'
             '\x00\x00\x00\x46')

    # Signature for REGF
    data2 = 'regf'

    # Random data
    data3 = '\x01\xfa\xe0\xbe\x99\x8e\xdb\x70\xea\xcc\x6b\xae\x2f\xf5\xa2\xe4'

    # Boundary scan test
    data4a = ('\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
              '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00PK')
    data4b = ('\x07\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
              '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Z')

    # Large buffer test
    data5_size = 1024 * 1024
    data5 = '\x00' * (data5_size - 4)
    data5 += 'PK\x07\x08'

    test_scanner = scanner.Scanner(store)

    total_data_size = len(data1)
    scan_state = test_scanner.StartScan(total_data_size=total_data_size)
    test_scanner.ScanBuffer(scan_state, data1, len(data1))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    scan_state = test_scanner.StartScan(total_data_size=None)
    test_scanner.ScanBuffer(scan_state, data1, len(data1))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    total_data_size = len(data2)
    scan_state = test_scanner.StartScan(total_data_size=total_data_size)
    test_scanner.ScanBuffer(scan_state, data2, len(data2))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    scan_state = test_scanner.StartScan(total_data_size=None)
    test_scanner.ScanBuffer(scan_state, data2, len(data2))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    total_data_size = len(data3)
    scan_state = test_scanner.StartScan(total_data_size=total_data_size)
    test_scanner.ScanBuffer(scan_state, data3, len(data3))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 0)

    scan_state = test_scanner.StartScan(total_data_size=None)
    test_scanner.ScanBuffer(scan_state, data3, len(data3))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 0)

    total_data_size = len(data4a) + len(data4b)
    scan_state = test_scanner.StartScan(total_data_size=total_data_size)
    test_scanner.ScanBuffer(scan_state, data4a, len(data4a))
    test_scanner.ScanBuffer(scan_state, data4b, len(data4b))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    scan_state = test_scanner.StartScan(total_data_size=None)
    test_scanner.ScanBuffer(scan_state, data4a, len(data4a))
    test_scanner.ScanBuffer(scan_state, data4b, len(data4b))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)

    total_data_size = len(data5)
    scan_state = test_scanner.StartScan(total_data_size=total_data_size)
    test_scanner.ScanBuffer(scan_state, data5, len(data5))
    test_scanner.StopScan(scan_state)

    self.assertEqual(len(scan_state.GetMatches()), 1)


if __name__ == '__main__':
  unittest.main()
