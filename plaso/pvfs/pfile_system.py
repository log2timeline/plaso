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

import os

from plaso.lib import errors
from plaso.lib import event
from plaso.pvfs import pfile_entry
from plaso.pvfs import vss

import pytsk3
import pyvshadow


class PFileSystem(object):
  """Class that implements the pfile system object interface."""

  PATH_SEPERATOR = u'/'

  def __init__(self, fscache):
    """Initialize the file system object."""
    super(PFileSystem, self).__init__()
    self._fscache = fscache

  def JoinPath(self, path_segments):
    """Joins the path segments into a path."""
    return self.PATH_SEPERATOR.join(path_segments)

  def SplitPath(self, path):
    """Splits the path into path segments."""
    return path.split(self.PATH_SEPERATOR)


class OsFileSystem(PFileSystem):
  """Class that implements a file system object using os."""

  PATH_SEPERATOR = os.path.sep
  TYPE_INDICATOR = 'OS'

  def __init__(self, fscache):
    """Initialize the file system object."""
    super(OsFileSystem, self).__init__(fscache)

  def GetRootFileEntry(self):
    """Retrieves the root file entry.

    Returns:
      A file entry (instance of OsFileEntry).
    """
    root_path_spec = event.EventPathSpec()
    root_path_spec.type = 'OS'
    root_path_spec.file_path = self.PATH_SEPERATOR

    return self.OpenFileEntry(root_path_spec)

  def Open(self, source_path):
    """Opens the file system.

    Args:
      source_path: Path of the source file or directory.
    """
    self._source_path = source_path

  def OpenFileEntry(self, path_spec):
    """Opens the file system.

    Args:
      path_spec: The path specification of the file entry.

    Returns:
      A file entry (instance of OsFileEntry).
    """
    # TODO: do we need to set root here?
    return pfile_entry.OsFileEntry(
        path_spec, root=None, fscache=self._fscache)


class TSKFileSystem(PFileSystem):
  """Class that implements a file system object using pytsk3."""

  TYPE_INDICATOR = 'TSK'

  def __init__(self, fscache):
    """Initialize the file system object."""
    super(TSKFileSystem, self).__init__(fscache)
    self._byte_offset = None
    self._source_path = None
    self._tsk_img = None
    self._volume = None
    self.tsk_fs = None

  def GetRootFileEntry(self):
    """Retrieves the root file entry.

    Returns:
      A file entry (instance of TSKFileEntry).
    """
    root_path_spec = event.EventPathSpec()
    root_path_spec.type = 'TSK'
    root_path_spec.file_path = self.PATH_SEPERATOR
    root_path_spec.image_inode = self.tsk_fs.info.root_inum
    root_path_spec.container_path = self._source_path
    root_path_spec.image_offset = self._byte_offset

    return self.OpenFileEntry(root_path_spec)

  def Open(self, source_path, byte_offset=0, store_number=None):
    """Opens the file system.

    Args:
      source_path: Path of the source file or directory.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
      store_number: Optional VSS store index number. The default is None.

    Raises:
      errors.UnableToOpenFilesystem: If it is not able to open the filesystem.
    """
    if store_number is not None:
      raise errors.UnableToOpenFilesystem(u'Unsupported store number.')

    self._source_path = source_path
    self._byte_offset = byte_offset

    try:
      self._tsk_img = pytsk3.Img_Info(self._source_path)
    except IOError as e:
      raise errors.UnableToOpenFilesystem(
          u'Unable to open image file with error: {0:s}'.format(e))

    try:
      self.tsk_fs = pytsk3.FS_Info(self._tsk_img, offset=self._byte_offset)
    except IOError as e:
      raise errors.UnableToOpenFilesystem(
          u'Unable to open file system with error: {0:s}'.format(e))

  def OpenFileEntry(self, path_spec):
    """Opens the file system.

    Args:
      path_spec: The path specification of the file entry.

    Returns:
      A file entry (instance of TSKFileEntry).
    """
    # TODO: do we need to set root here?
    return pfile_entry.TSKFileEntry(
        path_spec, root=None, fscache=self._fscache)


class VssFileSystem(TSKFileSystem):
  """Class that implements a file system object using pyvshadow."""

  TYPE_INDICATOR = 'VSS'

  def __init__(self, fscache):
    """Initialize the file system object."""
    super(VssFileSystem, self).__init__(fscache)
    self._store_number = None
    self._vshadow_volume = None

  def GetRootFileEntry(self):
    """Retrieves the root file entry.

    Returns:
      A file entry (instance of VssFileEntry).
    """
    root_path_spec = event.EventPathSpec()
    root_path_spec.type = 'VSS'
    root_path_spec.file_path = self.PATH_SEPERATOR
    root_path_spec.image_inode = self.tsk_fs.info.root_inum
    root_path_spec.container_path = self._source_path
    root_path_spec.image_offset = self._byte_offset
    root_path_spec.vss_store_number = self._store_number

    return self.OpenFileEntry(root_path_spec)

  def Open(self, source_path, byte_offset=0, store_number=None):
    """Opens the file system.

    Args:
      source_path: Path of the source file or directory.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
      store_number: Optional VSS store index number. The default is None.

    Raises:
      errors.UnableToOpenFilesystem: If it is not able to open the filesystem.
    """
    if store_number is None:
      raise errors.UnableToOpenFilesystem(u'Missing store number.')

    self._source_path = source_path
    self._byte_offset = byte_offset

    self._vshadow_volume = pyvshadow.volume()
    file_object = vss.VShadowVolume(source_path, self._byte_offset)
    self._vshadow_volume.open_file_object(file_object)
    vshadow_store = self._vshadow_volume.get_store(store_number)

    self._tsk_img = vss.VShadowImgInfo(vshadow_store)

    try:
      self.tsk_fs = pytsk3.FS_Info(self._tsk_img, offset=0)
    except IOError as e:
      raise errors.UnableToOpenFilesystem(
          u'Unable to open file system with error: {0:s}'.format(e))

  def OpenFileEntry(self, path_spec):
    """Opens the file system.

    Args:
      path_spec: The path specification of the file entry.

    Returns:
      A file entry (instance of VssFileEntry).
    """
    # TODO: do we need to set root here?
    return pfile_entry.VssFileEntry(
        path_spec, root=None, fscache=self._fscache)
