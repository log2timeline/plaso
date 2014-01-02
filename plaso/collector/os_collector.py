#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""The operating system collector object implementation."""

import logging
import os
import re

from plaso.collector import interface
from plaso.collector import os_helper
from plaso.pvfs import utils as pvfs_utils


class FileSystemPreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from mount points."""

  def __init__(self, pre_obj, source_path):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      source_path: Path of the source file or directory.
    """
    super(FileSystemPreprocessCollector, self).__init__(pre_obj)
    self._source_path = source_path

  def GetPaths(self, path_list):
    """Find the path if it exists.

    Args:
      path_list: A list of either regular expressions or expanded
                 paths (strings).

    Returns:
      A list of paths.
    """
    return os_helper.GetOsPaths(path_list, self._source_path)

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern.

    Args:
      path: the path.
      file_name: the file name pattern.

    Returns:
      A list of file names.
    """
    ret = []
    file_re = re.compile(r'^{0:s}$'.format(file_name), re.I | re.S)
    if path == os.path.sep:
      directory = self._source_path
      path_use = '.'
    else:
      directory = os.path.join(self._source_path, path)
      path_use = path

    try:
      for entry in os.listdir(directory):
        m = file_re.match(entry)
        if m:
          if os.path.isfile(os.path.join(directory, m.group(0))):
            ret.append(os.path.join(path_use, m.group(0)))
    except OSError as exception:
      logging.error(
          u'Unable to read directory: {0:s}, reason {1:s}'.format(
              directory, exception))
    return ret

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenOSFileEntry(os.path.join(self._source_path, path))

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return False
