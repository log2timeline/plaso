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
"""File for PyVFS migration to contain file entry related functionality."""

import abc
import bz2
import gzip
import logging
import os
import tarfile
import zipfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import registry
from plaso.lib import timelib
from plaso.lib import utils
from plaso.pvfs import pfile_io
from plaso.pvfs import pstats

import pytsk3


class BaseFileEntry(object):
  """Base class for a file entry object."""
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  TYPE = 'UNSET'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.

    Raises:
      errors.UnableToOpenFile: If this class supports the wrong driver for this
      file.
    """
    if pathspec.type != self.TYPE:
      raise errors.UnableToOpenFile('Unable to handle this file type.')

    super(BaseFileEntry, self).__init__()
    self._fscache = fscache
    self._stat_object = None
    self.file_object = None
    self.name = ''
    self.pathspec = pathspec

    if root:
      self.pathspec_root = root
    else:
      self.pathspec_root = pathspec

  def __enter__(self):
    """Make it work with the with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make it work with the with statement."""
    return

  def HasParent(self):
    """Check if the PathSpec defines a parent."""
    return hasattr(self.pathspec, 'nested_pathspec')

  @abc.abstractmethod
  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    This method reads the content of the PathSpec protobuf and opens
    the file entry up according to the driver the class supports.

    The file entry can be passed to the method if the file that needs to
    be opened is within another file.

    Args:
      file_entry: Optional parent file-like object. The default is None.

    Returns:
      A file-like object.
    """

  @abc.abstractmethod
  def Stat(self):
    """Return a Stats object that contains stats like information."""


class Bz2FileEntry(BaseFileEntry):
  """Provide a file-like object to a file compressed using BZ2."""

  TYPE = 'BZ2'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(Bz2FileEntry, self).__init__(pathspec, root=root, fscache=fscache)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if file_entry:
      try:
        file_entry.file_object.seek(0)
      except NotImplementedError:
        pass
      bzip2_file = bz2.BZ2File(file_entry.file_object, 'r')
      self.display_name = u'{}:{}{}'.format(
          file_entry.name, path_prepend, self.pathspec.file_path)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
      bzip2_file = bz2.BZ2File(self.pathspec.file_path, 'r')

    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)

    self.file_object = pfile_io.Bz2FileIO(bzip2_file)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      self._stat_object = pstats.Stats()
      self._stat_object.fs_type = 'BZ2 container'

    return self._stat_object


class GzipFileEntry(BaseFileEntry):
  """Provide a file-like object to a file compressed using GZIP."""

  TYPE = 'GZIP'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(GzipFileEntry, self).__init__(pathspec, root=root, fscache=fscache)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    if file_entry:
      file_entry.file_object.seek(0)
      gzip_file = gzip.GzipFile(fileobj=file_entry.file_object, mode='rb')
    else:
      gzip_file = gzip.GzipFile(
          filename=self.pathspec.file_path, mode='rb')

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    if file_entry:
      self.display_name = u'{}{}_uncompressed'.format(
          path_prepend, file_entry.name)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.name)

    # To get the size properly calculated.
    try:
      _ = gzip_file.read(4)
    except IOError as e:
      raise IOError(
          u'Unable to open GZIP file: {0:s} ({1:s}) with error: {2:s}'.format(
              self.name, self.display_name, e))
    gzip_file.rewind()
    try:
      self.size = gzip_file.size
    except AttributeError:
      self.size = 0

    self.file_object = pfile_io.GzipFileIO(gzip_file)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      self._stat_object = pstats.Stats()
      self._stat_object.size = self.size
      self._stat_object.fs_type = 'GZ File'

    return self._stat_object


class OsFileEntry(BaseFileEntry):
  """Class to provide a file-like object to a file stored on a filesystem."""

  TYPE = 'OS'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(OsFileEntry, self).__init__(pathspec, root=root, fscache=fscache)
    self.directory_entry_name = u''

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    file_object = open(self.pathspec.file_path, 'rb')
    self.name = self.pathspec.file_path
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if file_entry:
      self.display_name = u'{}:{}{}'.format(
          file_entry.name, path_prepend, self.name)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.name)

    self._stat_info = os.stat(self.name)
    self.file_object = pfile_io.OsFileIO(file_object, self._stat_info.st_size)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      self._stat_object = pstats.Stats()

      self._stat_object.mode = self._stat_info.st_mode
      self._stat_object.ino = self._stat_info.st_ino
      self._stat_object.dev = self._stat_info.st_dev
      self._stat_object.nlink = self._stat_info.st_nlink
      self._stat_object.uid = self._stat_info.st_uid
      self._stat_object.gid = self._stat_info.st_gid
      self._stat_object.size = self._stat_info.st_size

      if self._stat_info.st_atime > 0:
        self._stat_object.atime = self._stat_info.st_atime
      if self._stat_info.st_mtime > 0:
        self._stat_object.mtime = self._stat_info.st_mtime
      if self._stat_info.st_ctime > 0:
        self._stat_object.ctime = self._stat_info.st_ctime

      self._stat_object.fs_type = 'Unknown'
      self._stat_object.allocated = True

    return self._stat_object

  def GetSubFileEntries(self):
    """Retrieves the sub file entries.

    Yields:
      A sub file entry (instance of OsFileEntry).
    """
    if not os.path.isdir(self.pathspec.file_path):
      return

    for directory_entry in os.listdir(self.pathspec.file_path):
      directory_entry_path = os.path.join(
          self.pathspec.file_path, directory_entry)
      path_spec = event.EventPathSpec()
      path_spec.type = 'OS'
      path_spec.file_path = utils.GetUnicodeString(directory_entry_path)
      sub_file_entry = OsFileEntry(
          path_spec, root=self.pathspec_root, fscache=self._fscache)

      # Work-around for limitations of pfile, will be fixed by PyVFS.
      sub_file_entry.directory_entry_name = directory_entry
      yield sub_file_entry

  def IsAllocated(self):
    """Determines if the file entry is allocated."""
    return True

  def IsDirectory(self):
    """Determines if the file entry is a directory."""
    return os.path.isdir(self.pathspec.file_path)

  def IsFile(self):
    """Determines if the file entry is a file."""
    return os.path.isfile(self.pathspec.file_path)

  def IsLink(self):
    """Determines if the file entry is a link."""
    return os.path.islink(self.pathspec.file_path)


class TarFileEntry(BaseFileEntry):
  """Provide a file-like object to a file stored inside a TAR file."""

  TYPE = 'TAR'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(TarFileEntry, self).__init__(pathspec, root=root, fscache=fscache)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if file_entry:
      tar_file = tarfile.open(fileobj=file_entry.file_object, mode='r')
      self.display_name = u'{}:{}{}'.format(
          file_entry.name, path_prepend, self.pathspec.file_path)
    else:
      container_path = getattr(self.pathspec, 'container_path', '')
      if not container_path:
        raise IOError(
            u'[TAR] missing container path in path specification.')
      self.display_name = u'{}:{}{}'.format(
          container_path, path_prepend, self.pathspec.file_path)
      tar_file = tarfile.open(container_path, 'r')

    extracted_file_object = tar_file.extractfile(self.pathspec.file_path)
    if not extracted_file_object:
      raise IOError(
          u'Unable to extract file: {0:s} from TAR.'.format(
              self.pathspec.file_path))
    self.buffer = ''
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    self.size = extracted_file_object.size

    self.file_object = pfile_io.TarFileIO(extracted_file_object)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      self._stat_object = pstats.Stats()
      self._stat_object.fs_type = 'Tar container'

    return self._stat_object


class TSKFileEntry(BaseFileEntry):
  """Class to open up files using TSK."""

  TYPE = 'TSK'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(TSKFileEntry, self).__init__(pathspec, root=root, fscache=fscache)
    self.directory_entry_name = u''

  def _GetFileSystem(self):
    """Retrieves the file system object."""
    if not hasattr(self, '_fscache'):
      raise IOError(
          u'Unable to open file system missing file system cache.')

    image_offset = getattr(self.pathspec, 'image_offset', 0)
    return self._fscache.Open(
        self.pathspec.container_path, byte_offset=image_offset)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    This method reads the content of the PathSpec protobuf and opens
    the file entry object using the Sleuthkit (TSK).

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    if file_entry:
      raise IOError(u'Open with file entry not supported.')

    file_system = self._GetFileSystem()
    inode = getattr(self.pathspec, 'image_inode', 0)

    if not hasattr(self.pathspec, 'file_path'):
      self.pathspec.file_path = 'NA_NotProvided'

    self.file_object = pfile_io.TSKFileIO(
        file_system.tsk_fs, inode, self.pathspec.file_path)

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    self.size = self.file_object.size
    self.display_name = u'{}:{}{}'.format(
        self.pathspec.container_path, path_prepend,
        self.pathspec.file_path)
    if file_entry:
      self.display_name = u'{}:{}{}'.format(
          file_entry.name, path_prepend, self.display_name)

    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      file_system = self._GetFileSystem()
      self._stat_object = pstats.Stats()

      try:
        info = self.file_object.fileobj.info
        meta = info.meta
      except IOError:
        return self._stat_object

      if not meta:
        return self._stat_object

      self._stat_object.mode = getattr(meta, 'mode', None)
      self._stat_object.ino = getattr(meta, 'addr', None)
      self._stat_object.nlink = getattr(meta, 'nlink', None)
      self._stat_object.uid = getattr(meta, 'uid', None)
      self._stat_object.gid = getattr(meta, 'gid', None)
      self._stat_object.size = getattr(meta, 'size', None)
      self._stat_object.atime = getattr(meta, 'atime', None)
      self._stat_object.atime_nano = getattr(meta, 'atime_nano', None)
      self._stat_object.crtime = getattr(meta, 'crtime', None)
      self._stat_object.crtime_nano = getattr(meta, 'crtime_nano', None)
      self._stat_object.mtime = getattr(meta, 'mtime', None)
      self._stat_object.mtime_nano = getattr(meta, 'mtime_nano', None)
      self._stat_object.ctime = getattr(meta, 'ctime', None)
      self._stat_object.ctime_nano = getattr(meta, 'ctime_nano', None)
      self._stat_object.dtime = getattr(meta, 'dtime', None)
      self._stat_object.dtime_nano = getattr(meta, 'dtime_nano', None)
      self._stat_object.bkup_time = getattr(meta, 'bktime', None)
      self._stat_object.bkup_time_nano = getattr(meta, 'bktime_nano', None)

      flags = getattr(meta, 'flags', 0)

      # The flags are an instance of pytsk3.TSK_FS_META_FLAG_ENUM.
      if int(flags) & pytsk3.TSK_FS_META_FLAG_ALLOC:
        self._stat_object.allocated = True
      else:
        self._stat_object.allocated = False

      fs_type = str(file_system.tsk_fs.info.ftype)

      if fs_type.startswith('TSK_FS_TYPE'):
        self._stat_object.fs_type = fs_type[12:]
      else:
        self._stat_object.fs_type = fs_type

    return self._stat_object

  def GetSubFileEntries(self):
    """Retrieves the sub file entries.

    Yields:
      A sub file entry (instance of TSKFileEntry).
    """
    file_system = self._GetFileSystem()
    inode_number = getattr(self.pathspec, 'image_inode', None)
    if inode_number is not None:
      tsk_directory = file_system.tsk_fs.open_dir(inode=inode_number)
    else:
      tsk_directory = file_system.tsk_fs.open_dir(path=self.pathspec.file_path)

    for tsk_directory_entry in tsk_directory:
      image_inode = getattr(tsk_directory_entry.info.meta, 'addr', 0)
      # Ignore directory entries with an inode of 0.
      if image_inode == 0:
        continue

      # Pytsk returns a UTF-8 encoded byte string.
      name = tsk_directory_entry.info.name.name
      try:
        directory_entry_name = name.decode('utf8')
      except UnicodeError:
        logging.warning(u'Non UTF-8 directory entry name for inode: {}'.format(
            tsk_directory_entry.info.meta.addr))
        directory_entry_name = name.decode('utf8', 'ignore')

      # Ignore the directory entries . and ..
      if directory_entry_name in [u'.', u'..']:
        continue

      directory_entry_path = u'/'.join([
          self.pathspec.file_path, directory_entry_name])
      path_spec = event.EventPathSpec()

      if hasattr(self.pathspec, 'vss_store_number'):
        path_spec.type = 'VSS'
        path_spec.vss_store_number = self.pathspec.vss_store_number
      else:
        path_spec.type = 'TSK'

      path_spec.container_path = self.pathspec.container_path
      path_spec.image_offset = self.pathspec.image_offset
      path_spec.image_inode = image_inode
      path_spec.file_path = utils.GetUnicodeString(directory_entry_path)
      sub_file_entry = TSKFileEntry(
          path_spec, root=self.pathspec_root, fscache=self._fscache)

      # Work-around for limitations of pfile, will be fixed by PyVFS.
      sub_file_entry.directory_entry_name = directory_entry_name
      yield sub_file_entry

  def IsAllocated(self):
    """Determines if the file entry is allocated."""
    flags = getattr(self.file_object.fileobj.info.meta, 'flags', 0)
    return int(flags) & pytsk3.TSK_FS_META_FLAG_ALLOC

  def IsDirectory(self):
    """Determines if the file entry is a directory."""
    tsk_fs_meta_type = getattr(
        self.file_object.fileobj.info.meta, 'type',
        pytsk3.TSK_FS_META_TYPE_UNDEF)
    return tsk_fs_meta_type == pytsk3.TSK_FS_META_TYPE_DIR

  def IsFile(self):
    """Determines if the file entry is a file."""
    tsk_fs_meta_type = getattr(
        self.file_object.fileobj.info.meta, 'type',
        pytsk3.TSK_FS_META_TYPE_UNDEF)
    return tsk_fs_meta_type == pytsk3.TSK_FS_META_TYPE_REG

  def IsLink(self):
    """Determines if the file entry is a link."""
    tsk_fs_meta_type = getattr(
        self.file_object.fileobj.info.meta, 'type',
        pytsk3.TSK_FS_META_TYPE_UNDEF)
    return tsk_fs_meta_type == pytsk3.TSK_FS_META_TYPE_LNK


class VssFileEntry(TSKFileEntry):
  """Class to open up files in Volume Shadow Copies."""

  TYPE = 'VSS'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(VssFileEntry, self).__init__(pathspec, root=root, fscache=fscache)

  def _GetFileSystem(self):
    """Retrieves the file system object."""
    if not hasattr(self, '_fscache'):
      raise IOError(
          u'Unable to open file system missing file system cache.')

    if not hasattr(self.pathspec, 'vss_store_number'):
      raise IOError(
          u'Unable to open file system missing VSS store number.')

    image_offset = getattr(self.pathspec, 'image_offset', 0)
    return self._fscache.Open(
        self.pathspec.container_path, byte_offset=image_offset,
        store_number=self.pathspec.vss_store_number)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    file_object = super(VssFileEntry, self).Open(file_entry=file_entry)

    self.display_name = u'{0:s}:vss_store_{1:d}'.format(
        self.display_name, self.pathspec.vss_store_number)

    return file_object


class ZipFileEntry(BaseFileEntry):
  """Provide a file-like object to a file stored inside a ZIP file."""

  TYPE = 'ZIP'

  def __init__(self, pathspec, root=None, fscache=None):
    """Initializes the file entry object.

    Args:
      pathspec: The path specification (instance of transmission proto).
      root: Optional root path specification (instance of transmission proto).
            The default is None.
      fscache: Optional file system cache object. The default is None.
    """
    super(ZipFileEntry, self).__init__(pathspec, root=root, fscache=fscache)

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    if file_entry:
      try:
        zip_file = zipfile.ZipFile(file_entry.file_object, 'r')
      except zipfile.BadZipfile as e:
        raise IOError(
            u'Unable to open ZIP file, not a ZIP file?: {} [{}]'.format(
                file_entry.name, e))
      path_name = file_entry.name
    else:
      container_path = getattr(self.pathspec, 'container_path', '')
      if not container_path:
        raise IOError(
            u'[ZIP] missing container path in path specification.')
      path_name = container_path
      zip_file = zipfile.ZipFile(path_name, 'r')

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    if file_entry:
      self.display_name = u'{}:{}{}'.format(
          file_entry.display_name, path_prepend, self.pathspec.file_path)
    else:
      self.display_name = u'{}:{}{}'.format(
          path_name, path_prepend, self.pathspec.file_path)
    self.zipinfo = zip_file.getinfo(self.pathspec.file_path)

    try:
      _ = zip_file.open(self.pathspec.file_path, 'r')
    except (RuntimeError, zipfile.BadZipfile) as e:
      raise IOError(u'Unable to open ZIP file: {0:s} wiht error: {1:s}'.format(
          self.name, e))

    self.file_object = pfile_io.ZipFileIO(
        zip_file, self.pathspec.file_path, self.zipinfo.file_size)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if self._stat_object is None:
      self._stat_object = pstats.Stats()

      # TODO: Make this a proper stat element with as much information
      # as can be extracted.
      # Also confirm for sure that this is the correct timestamp and it is
      # stored in UTC (or if it is in local timezone, adjust it)
      self._stat_object.ctime = timelib.Timetuple2Timestamp(
          self.zipinfo.date_time)
      self._stat_object.size = self.zipinfo.file_size
      self._stat_object.fs_type = 'ZIP Container'

    return self._stat_object
