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

from plaso.lib import errors
from plaso.pvfs import pfile_system

import pytsk3


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


def GetPartitionMap(image_path):
  """Returns a list of dict objects representing partition information.

  Args:
    image_path: The path to the image file.

  Returns:
    A list that contains a dict object for each partition in the image. The
    dict contains the partition number (address), description of it alongside
    an offset and length of the partition size.
  """
  partition_map = []
  try:
    img = pytsk3.Img_Info(image_path)
  except IOError as exception:
    raise errors.UnableToOpenFilesystem(
        u'Unable to open image file with error: {0:s}'.format(exception))

  try:
    volume = pytsk3.Volume_Info(img)
  except IOError as exception:
    raise errors.UnableToOpenFilesystem(
        u'Unable to open file system with error: {0:s}'.format(exception))

  block_size = getattr(volume.info, 'block_size', 512)
  partition_map.append(block_size)

  for part in volume:
    partition_map.append({
        'address': part.addr,
        'description': part.desc,
        'offset': part.start,
        'length': part.len})

  return partition_map
