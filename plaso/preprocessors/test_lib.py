#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Preprocess plug-in related functions and classes for testing."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.vfs import fake_file_system


class PreprocessPluginTest(unittest.TestCase):
  """The unit test case for a preprocess plug-in object."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  def _BuildSingleFileFakeFileSystem(self, path, file_data):
    """Builds a single file fake file system.

    Args:
      path: The path of the file.
      file_data: The data of the file.

    Returns:
      The fake file system (instance of dvfvs.FakeFileSystem).
    """
    resolver_context = context.Context()
    file_system = fake_file_system.FakeFileSystem(
        resolver_context)

    file_system.AddFileEntry(
        u'/', file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    path_segments = path.split(u'/')
    for segment_index in range(2, len(path_segments)):
      path_segment = u'{0:s}'.format(
          u'/'.join(path_segments[:segment_index]))
      file_system.AddFileEntry(
          path_segment,
          file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    file_system.AddFileEntry(path, file_data=file_data)

    return file_system

  def _BuildSingleLinkFakeFileSystem(self, path, linked_path):
    """Builds a single link fake file system.

    Args:
      path: The path of the link.
      linked_path: The path that is linked.

    Returns:
      The fake file system (instance of dvfvs.FakeFileSystem).
    """
    resolver_context = context.Context()
    file_system = fake_file_system.FakeFileSystem(
        resolver_context)

    file_system.AddFileEntry(
        u'/', file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    path_segments = path.split(u'/')
    for segment_index in range(2, len(path_segments)):
      path_segment = u'{0:s}'.format(
          u'/'.join(path_segments[:segment_index]))
      file_system.AddFileEntry(
          path_segment,
          file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    file_system.AddFileEntry(
        path, file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_LINK,
        link_data=linked_path)

    return file_system
