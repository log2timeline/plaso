#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for plaso.output.pstorage."""

import os
import shutil
import tempfile
import unittest

from plaso.lib import pfilter
from plaso.lib import storage
from plaso.output import interface
from plaso.output import pstorage
from plaso.output import test_lib


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class PstorageTest(test_lib.LogOutputFormatterTestCase):
  """Tests for the plaso storage outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(PstorageTest, self).setUp()
    self.test_filename = os.path.join(u'test_data', u'psort_test.out')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    pfilter.TimeRangeCache.ResetTimeConstraints()

  def testOutput(self):
    with TempDirectory() as dirname:
      dump_file = os.path.join(dirname, u'plaso.db')
      # Copy events to pstorage dump.
      with storage.StorageFile(self.test_filename, read_only=True) as store:
        formatter = pstorage.PlasoStorageOutputFormatter(
            store, self._formatter_mediator, filehandle=dump_file)
        with interface.EventBuffer(
            formatter, check_dedups=False) as output_buffer:
          event_object = store.GetSortedEntry()
          while event_object:
            output_buffer.Append(event_object)
            event_object = store.GetSortedEntry()

      # Make sure original and dump have the same events.
      original = storage.StorageFile(self.test_filename, read_only=True)
      dump = storage.StorageFile(dump_file, read_only=True)
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

      for original_str, dump_str in zip(
          sorted(original_list), sorted(dump_list)):
        self.assertEqual(original_str, dump_str)


if __name__ == '__main__':
  unittest.main()
