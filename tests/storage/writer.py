#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage writer."""

import unittest

from plaso.storage import writer

from tests.storage import test_lib


class StorageWriterTest(test_lib.StorageTestCase):
  """Tests for the storage writer."""

  # pylint: disable=protected-access

  # TODO: add tests for number_of_analysis_reports property
  # TODO: add tests for number_of_analysis_warnings property
  # TODO: add tests for number_of_event_sources property
  # TODO: add tests for number_of_event_tags property
  # TODO: add tests for number_of_events property
  # TODO: add tests for number_of_extraction_warnings property
  # TODO: add tests for number_of_preprocessing_warnings property
  # TODO: add tests for number_of_recovery_warnings property

  def testRaiseIfNotWritable(self):
    """Tests the _RaiseIfNotWritable function."""
    storage_writer = writer.StorageWriter()

    with self.assertRaises(IOError):
      storage_writer._RaiseIfNotWritable()

  # TODO: add tests for AddAttributeContainer method
  # TODO: add tests for AddOrUpdateEventTag method
  # TODO: add tests for Close method
  # TODO: add tests for UpdateAttributeContainer method


if __name__ == '__main__':
  unittest.main()
