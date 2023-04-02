#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the operating system independent (generic) preprocessor plugins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec

from plaso.preprocessors import generic
from plaso.preprocessors import mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class DetermineOperatingSystemPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the plugin to determine the operating system."""

  def testCollect(self):
    """Tests the Collect function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = shared_test_lib.GetTestFilePath(['SOFTWARE'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SOFTWARE', test_file_path)
    test_file_path = shared_test_lib.GetTestFilePath(['SYSTEM'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SYSTEM', test_file_path)

    storage_writer = fake_writer.FakeStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    mount_point = fake_path_spec.FakePathSpec(location='/')
    searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

    plugin = generic.DetermineOperatingSystemPlugin()

    storage_writer.Open()

    try:
      plugin.Collect(
          test_mediator, None, searcher, file_system_builder.file_system)
    finally:
      storage_writer.Close()

    operating_system = test_mediator.GetValue('operating_system')
    self.assertEqual(operating_system, 'Windows NT')


if __name__ == '__main__':
  unittest.main()
