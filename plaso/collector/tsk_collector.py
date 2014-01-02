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
"""The SleuthKit collector object implementation."""

import re

from plaso.collector import interface
from plaso.collector import tsk_helper
from plaso.lib import errors
from plaso.pvfs import pvfs
from plaso.pvfs import utils as pvfs_utils

import pytsk3


class TSKFilePreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from TSK images."""

  _BYTES_PER_SECTOR = 512

  def __init__(self, pre_obj, source_path, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      source_path: Path of the source image file.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(TSKFilePreprocessCollector, self).__init__(pre_obj)
    self._source_path = source_path
    self._image_offset = byte_offset
    self._fscache = pvfs.FilesystemCache()
    self._fs_obj = self._fscache.Open(source_path, byte_offset=byte_offset)

  def GetPaths(self, path_list):
    """Find the path if it exists.

    Args:
      path_list: A list of either regular expressions or expanded
                 paths (strings).

    Returns:
      A list of paths.
    """
    return tsk_helper.GetTSKPaths(path_list, self._fs_obj)

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^{0:s}$'.format(file_name), re.I | re.S)
    try:
      directory = self._fs_obj.fs.open_dir(path)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open directory: {0:s} with error: {1:s}'.format(path, e))

    for tsk_file in directory:
      try:
        f_type = tsk_file.info.meta.type
        name = tsk_file.info.name.name
      except AttributeError:
        continue
      if f_type == pytsk3.TSK_FS_META_TYPE_REG:
        m = file_re.match(name)
        if m:
          ret.append(u'{0:s}/{1:s}'.format(path, name))

    return ret

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenTskFileEntry(
        path, self._source_path,
        int(self._image_offset / self._BYTES_PER_SECTOR), self._fscache)

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return True


class VSSFilePreprocessCollector(TSKFilePreprocessCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, source_path, store_number, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      source_path: Path of the source image file.
      store_number: The VSS store index number.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(VSSFilePreprocessCollector, self).__init__(
        pre_obj, source_path, byte_offset=byte_offset)
    self._store_number = store_number
    self._fscache = pvfs.FilesystemCache()
    self._fs_obj = self._fscache.Open(
        source_path, byte_offset=byte_offset, store_number=store_number)

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenVssFileEntry(
        path, self._source_path, self._store_number,
        int(self._source_path / self._BYTES_PER_SECTOR), self._fscache)
