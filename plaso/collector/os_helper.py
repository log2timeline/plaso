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
"""The operating system helper functions."""

import logging
import os

from plaso.lib import errors
from plaso.pvfs import pstats


def GetOsDirectoryStat(directory_path):
  """Return a stat object for an OS directory object.

  Args:
    directory_path: Path to the directory.

  Returns:
    A stat object for the directory.
  """
  ret = pstats.Stats()
  stat = os.stat(directory_path)

  ret.full_path = directory_path
  ret.display_path = directory_path
  ret.mode = stat.st_mode
  ret.ino = stat.st_ino
  ret.dev = stat.st_dev
  ret.nlink = stat.st_nlink
  ret.uid = stat.st_uid
  ret.gid = stat.st_gid
  ret.size = stat.st_size
  if stat.st_atime > 0:
    ret.atime = stat.st_atime
  if stat.st_mtime > 0:
    ret.mtime = stat.st_mtime
  if stat.st_ctime > 0:
    ret.ctime = stat.st_ctime
  ret.fs_type = 'Unknown'
  ret.allocated = True

  return ret


def GetOsPaths(path_list, mount_point):
  """Find the path if it exists.

  Args:
    path_list: A list of either regular expressions or expanded
               paths (strings).
    mount_point: The path to the mount point or base directory.

  Returns:
    A list of paths.
  """
  paths = []

  for part in path_list:
    if isinstance(part, (str, unicode)):
      if part == '/':
        part = os.path.sep

      # TODO: this is inefficient make sure to replace with an approach
      # that uses hashing e.g. storing the path as hash and counting
      # occurances and returning paths.keys() as a list.
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
        for entry in os.listdir(os.path.join(mount_point, path)):
          m = part.match(entry)
          if m:
            paths.append(os.path.join(path, m.group(0)))
            found_path = True
      if not found_path:
        raise errors.PathNotFound(
            u'Path not found inside %s/%s' % (mount_point, paths))

  for real_path in paths:
    if not os.path.isdir(os.path.join(mount_point, real_path)):
      logging.warning(
          u'File path does not seem to exist (%s/%s)', mount_point,
          real_path)
      continue

    ret = real_path
    if real_path[0] == '.':
      ret = real_path[2:]

    yield ret
