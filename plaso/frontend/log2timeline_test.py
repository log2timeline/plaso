#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline front-end."""

import os
import shutil
import tempfile
import unittest

from plaso.frontend import frontend
from plaso.frontend import log2timeline
from plaso.frontend import test_lib
from plaso.lib import pfilter
from plaso.lib import storage

# We access some protected methods in order to test them.
# pylint: disable=protected-access


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the log2timeline front-end."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    # This is necessary since TimeRangeCache uses class members.
    # TODO: remove this work around and properly fix TimeRangeCache.
    pfilter.TimeRangeCache.ResetTimeConstraints()

    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testGetStorageInformation(self):
    """Tests the get storage information function."""
    test_front_end = log2timeline.Log2TimelineFrontend()

    options = frontend.Options()
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    storage_file_path = os.path.join(self._temp_directory, u'plaso.db')

    test_front_end.ParseOptions(options)
    test_front_end.SetStorageFile(storage_file_path=storage_file_path)

    test_front_end.ProcessSource(options)

    try:
      storage_file = storage.StorageFile(storage_file_path, read_only=True)
    except IOError:
      self.fail(u'Not a storage file.')

    # Make sure we can read an event out of the storage.
    event_object = storage_file.GetSortedEntry()
    self.assertIsNotNone(event_object)

  def testPluginData(self):
    """Tests the _GetPluginData method, which provides the info function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    plugin_info = test_front_end._GetPluginData()

    self.assertIn(u'Hashers', plugin_info)
    available_hasher_names = []
    for hasher_info in plugin_info[u'Hashers']:
      available_hasher_names.append(hasher_info[0])
    self.assertIn(u'sha256', available_hasher_names)
    self.assertIn(u'sha1', available_hasher_names)

    self.assertIn(u'Parsers', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parsers'])
    self.assertIn(u'Plugins', plugin_info)
    self.assertIsNotNone(plugin_info[u'Plugins'])

    # TODO: add more tests that cover more of the functionality of the frontend.


if __name__ == '__main__':
  unittest.main()
