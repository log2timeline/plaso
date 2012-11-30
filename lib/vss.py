#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a simple library to read files stored in VSS."""
import os

import pytsk3

__pychecker__ = 'no-funcdoc'


class VShadowImgInfo(pytsk3.Img_Info):
  """Extending the TSK Img_Info to allow VSS images to be read in."""

  def __init__(self, store):
    self._store = store
    super(VShadowImgInfo, self).__init__()

  # Implementing an interface
  def read(self, offset, size):  # pylint: disable=C6409
    self._store.seek(offset)
    return self._store.read(size)

  # Implementing an interface
  def get_size(self):  # pylint: disable=C6409
    return self._store.get_size()


class VShadowVolume(object):
  """Disk file implementation faking volume file.

  pyvhsadow does not support disk images, only volume based ones.
  In order for us to be able to use disk images we need to provide
  an interface that exposes volumes inside of a disk image.
  """

  SECTOR_SIZE = 512

  def __init__(self, file_path, offset=0):
    """Provide a file like object of a volume inside a disk image.

    Args:
      file_path: String, denoting the file path to the disk image.
      offset: An offset in bytes to the volume within the disk.
    """
    self._block_size = 0
    self._offset_start = 0
    self._orig_offset = offset

    ofs = int(offset / self.SECTOR_SIZE)
    self._block_size, self._image_size = self.GetImageSize(file_path, ofs)

    self._fh = open(file_path, 'rb')
    self._fh.seek(0, 2)
    self._fh_size = self._fh.tell()
    self._image_offset = ofs

    if self._block_size:
      self._offset_start = self._image_offset * self._block_size
      self._fh.seek(self._offset_start, 0)

  def GetImageSize(self, file_path, offset):
    """Read the partition information to gather volume size."""
    if not offset:
      return 0, 0

    __pychecker__ = 'unusednames=self'
    img = pytsk3.Img_Info(file_path)
    try:
      volume = pytsk3.Volume_Info(img)
    except IOError:
      return 0, 0

    size = 0
    for vol in volume:
      if vol.start == offset:
        size = vol.len
        break

    __pychecker__ = 'no-objattrs'
    size *= volume.info.block_size
    return volume.info.block_size, size

  def read(self, size=None):  # pylint: disable=C6409
    """"Return read bytes from volume as denoted by the size parameter."""
    if not self._orig_offset:
      return self._fh.read(size)

    # Check upper bounds, we need to return empty values for above bounds.
    if size + self.tell() > self._offset_start + self._image_size:
      size = self._offset_start + self._image_size - self.tell()

      if size < 1:
        return ''

    return self._fh.read(size)

  def get_size(self):  # pylint: disable=C6409
    """Return the size in bytes of the volume."""
    if self._block_size:
      return self._block_size * self._image_size

    return self._fh_size

  def close(self):  # pylint: disable=C6409
    self._fh.close()

  def seek(self, offset, whence=os.SEEK_SET):  # pylint: disable=C6409
    """Seek into the volume."""
    if not self._block_size:
      self._fh.seek(offset, whence)
      return

    ofs = 0
    abs_ofs = 0
    if whence == os.SEEK_SET:
      ofs = offset + self._offset_start
      abs_ofs = ofs
    elif whence == os.SEEK_CUR:
      ofs = offset
      abs_ofs = self.tell() + ofs
    elif whence == os.SEEK_END:
      size_diff = self._fh_size - (self._offset_start + self._image_size)
      ofs = offset - size_diff
      abs_ofs = self._image_size + self._offset_start + offset
    else:
      raise RuntimeError('Illegal whence value %s' % whence)

    # check boundary
    if abs_ofs < self._offset_start:
      raise IOError('Invalid seek, out of bounds. Seek before start.')

    self._fh.seek(ofs, whence)

  def tell(self):  # pylint: disable=C6409
    if not self._block_size:
      return self._fh.tell()

    return self._fh.tell() - self._offset_start

  def get_offset(self):  # pylint: disable=C6409
    return self.tell()
