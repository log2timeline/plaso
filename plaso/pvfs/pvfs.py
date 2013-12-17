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
"""File for PyVFS migration to contain file system related functionality."""

from plaso.lib import errors
from plaso.pvfs import vss

import pytsk3
import pyvshadow


# TODO: Add support for "carving" embedded files
# out using the embedded portion of the proto.
class FilesystemContainer(object):
  """A container for the filesystem and image."""

  def __init__(self, fs, img, path, offset=0, volume=None, store_nr=-1):
    """Container for objects needed to cache a filesystem connection.

    Args:
      fs: A FS_Info object.
      img: An Img_Info object.
      path: The path to the image.
      offset: An offset to the image.
      volume: If this is a VSS, the volume object.
      store_nr: If this is a VSS, the store number.
    """
    self.fs = fs
    self.img = img
    self.path = path
    self.offset = offset
    self.volume = volume
    self.store_nr = store_nr


class FilesystemCache(object):
  """A class to open and store filesystem objects in cache."""

  def __init__(self):
    """Set up the filesystem cache."""
    self.cached_filesystems = {}

  def Open(self, path, offset=0, store_nr=-1):
    """Return a filesystem from the cache.

    Args:
      path: Full path to the image file.
      offset: Offset in bytes to the start of the volume.
      store_nr: If this is a VSS then the store nr.

    Returns:
      If the filesystem object is cached it will be returned,
      otherwise it will be opened and then returned.
    """
    fs_hash = u'{0:s}:{1:d}:{2:d}'.format(path, offset, store_nr)

    if fs_hash in self.cached_filesystems:
      return self.cached_filesystems[fs_hash]

    if store_nr >= 0:
      fs = OpenVssImage(path, store_nr, offset)
    else:
      fs = OpenTskImage(path, offset)

    self.cached_filesystems[fs_hash] = fs
    return fs


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
  except IOError as e:
    raise errors.UnableToOpenFilesystem(
        u'Unable to open image file. [%s]' % e)

  try:
    volume = pytsk3.Volume_Info(img)
  except IOError:
    raise errors.UnableToOpenFilesystem(
        u'Unable to open the disk image [%s]' % image_path)

  block_size = getattr(volume.info, 'block_size', 512)
  partition_map.append(block_size)

  for part in volume:
    partition_map.append({
        'address': part.addr,
        'description': part.desc,
        'offset': part.start,
        'length': part.len})

  return partition_map


def OpenTskImage(image_path, offset=0):
  """Open and store a regular TSK image in cache.

  Args:
    image_path: Full path to the image file.
    offset: Offset in bytes to the start of the volume.

  Returns:
    A FilesystemContainer object that stores a cache of the FS.

  Raises:
    errors.UnableToOpenFilesystem: If it is not able to open the filesystem.
  """
  try:
    img = pytsk3.Img_Info(image_path)
  except IOError as e:
    raise errors.UnableToOpenFilesystem(
        u'Unable to open image file. [%s]' % e)

  try:
    fs = pytsk3.FS_Info(img, offset=offset)
  except IOError as e:
    raise errors.UnableToOpenFilesystem(
        u'Unable to mount image, wrong offset? [%s]' % e)

  return FilesystemContainer(fs, img, image_path, offset)


def OpenVssImage(image_path, store_nr, offset=0):
  """Open and store a VSS image in cache.

  Args:
    image_path: Full path to the image file.
    store_nr: Integer, indicating the VSS store number.
    offset: Offset in bytes to the start of the volume.

  Returns:
    A FilesystemContainer object that stores a cache of the FS.
  """
  volume = pyvshadow.volume()
  fh = vss.VShadowVolume(image_path, offset)
  volume.open_file_object(fh)
  store = volume.get_store(store_nr)
  img = vss.VShadowImgInfo(store)
  fs = pytsk3.FS_Info(img)

  return FilesystemContainer(fs, img, image_path, offset, volume, store_nr)
