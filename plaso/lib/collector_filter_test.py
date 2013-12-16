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
"""Contains the unit tests for the filter collection mechanism of Plaso."""
import os
import logging
import tempfile
import unittest

from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import os_preprocess
from plaso.lib import preprocess

from plaso.proto import transmission_pb2


class CollectionFilterTest(unittest.TestCase):
  """Test CollectionFilter check."""

  def testFilter(self):
    """Run the tests."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      # 2 hits.
      fh.write('/test_data/testdir/filter_.+.txt\n')
      # A single hit.
      fh.write('/test_data/.+evtx\n')
      # A single hit.
      fh.write('/AUTHORS\n')
      fh.write('/does_not_exist/some_file_[0-9]+txt\n')
      # This should not compile properly, missing file information.
      fh.write('failing/\n')
      # This should not fail during initial loading, but fail later on.
      fh.write('bad re (no close on that parenthesis/file\n')

    pre_obj = preprocess.PlasoPreprocess()
    my_collector = os_preprocess.FileSystemCollector(pre_obj, './')
    my_filter = collector_filter.CollectionFilter(my_collector, filter_name)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', filter_name, e)

    # This filter will contain all the filter lines, even those that will fail
    # during finding pathspecs, yet there is one that will fail, so we should
    # have five hits.
    filter_list = my_filter.BuildFiltersFromProto()
    self.assertEquals(len(filter_list), 5)

    pathspecs = list(my_filter.GetPathSpecs())
    # One evtx, one AUTHORS, two filter_*.txt files, total 4 files.
    self.assertEquals(len(pathspecs), 4)

    with self.assertRaises(errors.BadConfigOption):
      _ = collector_filter.CollectionFilter(
          my_collector, 'thisfiledoesnotexist')

    # Build a proto using the same filter criteria as above.
    proto = transmission_pb2.PathFilter()
    proto.filter_string.append('failing/')
    proto.filter_string.append('/AUTHORS')
    proto.filter_string.append('/does_not_exist/some_file_[0-9]+txt')
    proto.filter_string.append('/test_data/.+evtx')
    proto.filter_string.append('/test_data/testdir/filter_.+.txt')
    proto.filter_string.append('bad re (no close on that parenthesis/file')

    proto_filter = collector_filter.CollectionFilter(my_collector, proto)
    proto_list = proto_filter.BuildFiltersFromProto()
    self.assertEquals(len(proto_list), 5)

    proto_serialized_filter = collector_filter.CollectionFilter(
        my_collector, proto.SerializeToString())
    proto_serialized_list = proto_serialized_filter.BuildFiltersFromProto()
    self.assertEquals(len(proto_serialized_list), 5)

    self.assertEquals((u'', u'AUTHORS'), proto_serialized_list[0])
    self.assertEquals((u'/does_not_exist', u'some_file_[0-9]+txt'),
                      proto_serialized_list[1])


if __name__ == '__main__':
  unittest.main()
