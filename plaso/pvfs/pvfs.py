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
"""File for PyVFS migration to contain generic VFS related functionality."""

from plaso.pvfs import pfile_system


class FilesystemCache(object):
  """A class to open and store filesystem objects in cache."""

  def __init__(self):
    """Set up the filesystem cache."""
    super(FilesystemCache, self).__init__()
    self.cached_filesystems = {}

  def Open(self, source_path, byte_offset=0, store_number=None):
    """Return a filesystem from the cache.

    Args:
      source_path: Path of the source file or directory.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
      path: Full path to the image file.
      store_number: Optional VSS store index number. The default is None.

    Returns:
      If the file system object is cached it will be returned,
      otherwise it will be opened and then returned.
    """
    if store_number is None:
      file_system_hash = u'{0:s}:{1:d}:-1'.format(source_path, byte_offset)
    else:
      file_system_hash = u'{0:s}:{1:d}:{2:d}'.format(
          source_path, byte_offset, store_number)

    if file_system_hash not in self.cached_filesystems:
      if store_number is not None:
        file_system = pfile_system.VssFileSystem(self)
      else:
        file_system = pfile_system.TSKFileSystem(self)

      file_system.Open(
          source_path, byte_offset=byte_offset, store_number=store_number)

      self.cached_filesystems[file_system_hash] = file_system

    return self.cached_filesystems[file_system_hash]
