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


def GetGenericCollector(proc_queue, stor_queue, source_path):
  """Factory function to retrieve a generic collector object.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    source_path: Path of the source file or directory.
  """
  return generic_collector.GenericCollector(proc_queue, stor_queue, source_path)


def GetGenericPreprocessCollector(pre_obj, source_path):
  """Factory function to retrieve a generic preprocess collector object.

  Args:
    pre_obj: The preprocessing object.
    source_path: Path of the source file or directory.

  Returns:
    A preprocess collector object (instance of PreprocessCollector).
  """
  return generic_collector.GenericPreprocessCollector(pre_obj, source_path)
