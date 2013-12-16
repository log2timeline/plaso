#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""File for PyVFS migration to contain all OS specific preprocess code."""

import logging
import os
import re

from plaso.lib import errors
from plaso.lib import putils
from plaso.lib import preprocess


class FileSystemCollector(preprocess.Collector):
  """A wrapper around collecting files from mount points."""

  def __init__(self, pre_obj, mount_point):
    """Initalize the filesystem collector."""
    super(FileSystemCollector, self).__init__(pre_obj)
    self._mount_point = mount_point

  def GetPaths(self, path_list):
    """Find the path on the OS if it exists."""
    paths = []

    for part in path_list:
      if isinstance(part, (str, unicode)):
        if part == '/':
          part = os.path.sep

        if len(paths):
          for index, path in enumerate(paths):
            paths[index] = os.path.join(path, part)
        else:
          paths.append(part)

      else:
        found_path = False
        if not paths:
          paths.append('.')

        old_paths = list(paths)
        paths = []
        for path in old_paths:
          for entry in os.listdir(os.path.join(self._mount_point, path)):
            m = part.match(entry)
            if m:
              paths.append(os.path.join(path, m.group(0)))
              found_path = True
        if not found_path:
          raise errors.PathNotFound(
              u'Path not found inside %s/%s' % (self._mount_point, paths))

    for real_path in paths:
      if not os.path.isdir(os.path.join(self._mount_point, real_path)):
        logging.warning(
            u'File path does not seem to exist (%s/%s)', self._mount_point,
            real_path)
        continue

      ret = real_path
      if real_path[0] == '.':
        ret = real_path[2:]

      yield ret

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^%s$' % file_name, re.I | re.S)
    if path == os.path.sep:
      directory = self._mount_point
      path_use = '.'
    else:
      directory = os.path.join(self._mount_point, path)
      path_use = path

    try:
      for entry in os.listdir(directory):
        m = file_re.match(entry)
        if m:
          if os.path.isfile(os.path.join(directory, m.group(0))):
            ret.append(os.path.join(path_use, m.group(0)))
    except OSError as e:
      logging.error(u'Unable to read directory: %s, reason %s', directory, e)
    return ret

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return putils.OpenOSFile(os.path.join(self._mount_point, path))
