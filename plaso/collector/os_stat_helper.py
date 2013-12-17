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
"""The operating system stat helper functions."""

import os

from plaso.lib import pfile


def GetOsDirectoryStat(directory_path):
  """Return a stat object for an OS directory object.

  Args:
    directory_path: Path to the directory.

  Returns:
    A stat object for the directory.
  """
  ret = pfile.Stats()
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
