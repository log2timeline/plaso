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
"""The collector object factory."""
# Note that this is not a real factory class but code that provides
# factory helper functions for the PyVFS migration.

from plaso.collector import generic_collector
from plaso.collector import os_collector
from plaso.collector import tsk_collector


def GetFileSystemPreprocessCollector(pre_obj, source_path):
  """Factory function to retrieve an image preprocess collector object.

  Args:
    pre_obj: The pre-processing object.
    source_path: Path of the source file or directory.

  Returns:
    A preprocess collector object (instance of PreprocessCollector).
  """
  return os_collector.FileSystemPreprocessCollector(pre_obj, source_path)


def GetImagePreprocessCollector(
    pre_obj, source_path, byte_offset=0, vss_store_number=None):
  """Factory function to retrieve an image preprocess collector object.

  Args:
    pre_obj: The pre-processing object.
    source_path: Path of the source image file.
    byte_offset: Optional byte offset into the image file if this is a disk
                 image. The default is 0.
    vss_store_number: Optional VSS store index number. The default is None.

  Returns:
    A preprocess collector object (instance of PreprocessCollector).
  """
  if vss_store_number is not None:
    return tsk_collector.VSSFilePreprocessCollector(
        pre_obj, source_path, vss_store_number, byte_offset=byte_offset)
  return tsk_collector.TSKFilePreprocessCollector(
      pre_obj, source_path, byte_offset=byte_offset)


def GetGenericCollector(proc_queue, stor_queue, source_path):
  """Factory function to retrieve a generic collector object.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    source_path: Path of the source file or directory.
  """
  return generic_collector.GenericCollector(proc_queue, stor_queue, source_path)
