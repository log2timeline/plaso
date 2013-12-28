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
"""Tests for plaso.output.pstorage."""
import os
import tempfile
import unittest

from plaso.lib import output
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.output import pstorage   # pylint: disable-msg=unused-import


class PstorageTest(unittest.TestCase):
  def setUp(self):
    self.test_filename = os.path.join('test_data', 'psort_test.out')
    self.dump_file = tempfile.NamedTemporaryFile(delete=True)
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None
    pfilter.TimeRangeCache.ResetTimeConstraints()

  def testOutput(self):
    # Copy events to pstorage dump.
    with storage.PlasoStorage(self.test_filename, read_only=True) as store:
      formatter_cls = output.GetOutputFormatter('Pstorage')
      formatter = formatter_cls(store, self.dump_file)
      with output.EventBuffer(formatter, check_dedups=False) as output_buffer:
        event_object = formatter.FetchEntry()
        while event_object:
          output_buffer.Append(event_object)
          event_object = formatter.FetchEntry()

    # Make sure original and dump have the same events.
    original = storage.PlasoStorage(self.test_filename, read_only=True)
    dump = storage.PlasoStorage(self.dump_file.name, read_only=True)
    event_object_original = original.GetSortedEntry()
    event_object_dump = dump.GetSortedEntry()
    original_list = []
    dump_list = []

    while event_object_original:
      original_list.append(event_object_original.EqualityString())
      dump_list.append(event_object_dump.EqualityString())
      event_object_original = original.GetSortedEntry()
      event_object_dump = dump.GetSortedEntry()

    self.assertFalse(event_object_dump)

    for original_str, dump_str in zip(sorted(original_list), sorted(dump_list)):
      self.assertEqual(original_str, dump_str)


if __name__ == '__main__':
  unittest.main()
