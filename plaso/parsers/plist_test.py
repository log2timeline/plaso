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
"""This file contains the unit tests for the Plist parsing in Plaso."""

import os
import unittest

from plaso.lib import preprocess
from plaso.parsers import plist


class PlistTest(unittest.TestCase):
  """The unit test for plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = 'test_data'
    self.plist_binary = os.path.join(self.base_path, 'plist_binary')
    self.pre = preprocess.PlasoPreprocess()

  def testParse(self):
    """Parse sample BT Plist file there should be 12 events of known values."""
    parser = plist.PlistParser(self.pre)

    with open(self.plist_binary) as fd:
      timestamps, roots, keys = zip(*[(x.timestamp, x.root, x.key) for x in
                                      parser.Parse(fd)])

      # Ensures all 12 timestamps were correctly parsed.
      correct_ts = [1345251192000000, 1351827808000000, 1345251268000000,
                    1351818803000000, 1351819298000000, 1351818797000000,
                    1301012201000000, 1302199013000000, 1341957900000000,
                    1350666391000000, 1350666385000000, 1341957896000000]
      self.assertTrue(set(correct_ts) == set(timestamps))
      self.assertEquals(12, len(timestamps))

      # Ensures expected devices are parsed.
      correct_roots = frozenset(['/DeviceCache/00-0d-fd-00-00-00',
                                 '/DeviceCache/44-00-00-00-00-00',
                                 '/DeviceCache/44-00-00-00-00-01',
                                 '/DeviceCache/44-00-00-00-00-02',
                                 '/DeviceCache/44-00-00-00-00-03',
                                 '/DeviceCache/44-00-00-00-00-04'])
      self.assertTrue(correct_roots == set(roots))
      self.assertEquals(12, len(roots))

      # Ensures expected key values are parsed.
      correct_keys = frozenset(['LastInquiryUpdate', 'LastServicesUpdate',
                                'LastNameUpdate'])
      self.assertTrue(correct_keys == set(keys))
      self.assertEquals(12, len(keys))

if __name__ == '__main__':
  unittest.main()
