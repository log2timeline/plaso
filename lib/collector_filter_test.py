#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
import tempfile
import unittest

from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import preprocess


class CollectionFilterTest(unittest.TestCase):
  """Test CollectionFilter check."""

  def testFilter(self):
    """Run the tests."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/lib/collector_.+\n')
      fh.write('/test_data/.+evtx\n')
      fh.write('/AUTHORS\n')
      fh.write('/does_not_exist/some_file_[0-9]+txt\n')
      # This should not compile properly, missing file information.
      fh.write('failing/\n')
      # This should not fail during initial loading, but fail later on.
      fh.write('bad re (no close on that parenthesis/file\n')

    pre_obj = preprocess.PlasoPreprocess()
    my_collector = preprocess.FileSystemCollector(
        pre_obj, './')
    my_filter = collector_filter.CollectionFilter(my_collector, filter_name)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', filter_name, e)

    # This filter will contain all the filter lines, even those that will fail
    # during finding pathspecs, yet there is one that will fail, so we should
    # have five hits.
    self.assertEquals(len(my_filter._filters), 5)

    pathspecs = list(my_filter.GetPathSpecs())
    # One evtx, one AUTHORS, three collector_* files, total five files.
    self.assertEquals(len(pathspecs), 5)

    with self.assertRaises(errors.BadConfigOption):
      _ = collector_filter.CollectionFilter(
          my_collector, 'thisfiledoesnotexist')


if __name__ == '__main__':
  unittest.main()
