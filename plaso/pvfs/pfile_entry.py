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
    self._stat = None
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

  def __exit__(self, dummy_type, dummy_value, dummy_traceback):
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
    if getattr(self, '_stat', None):
      return self._stat

    stats_object = pstats.Stats()
    stats_object.fs_type = 'BZ2 container'
    self._stat = stats_object
    return stats_object


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
      dn = self.display_name
      raise IOError('Not able to open the GZIP file %s -> %s [%s]' % (
          self.name, dn, e))
    gzip_file.rewind()
    try:
      self.size = gzip_file.size
    except AttributeError:
      self.size = 0

    self.file_object = pfile_io.GzipFileIO(gzip_file)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    stats_object = pstats.Stats()
    stats_object.size = self.size
    stats_object.fs_type = 'GZ File'

    self._stat = stats_object
    return stats_object


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
    self._stat_object = None

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
      directory_entry = os.path.join(self.pathspec.file_path, directory_entry)
      path_spec = event.EventPathSpec()
      path_spec.type = 'OS'
      path_spec.file_path = utils.GetUnicodeString(directory_entry)
      yield OsFileEntry(
          path_spec, root=self.pathspec_root, fscache=self._fscache)

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
          u'[TAR] File %s empty or unable to open.' % self.pathspec.file_path)
    self.buffer = ''
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    self.size = extracted_file_object.size

    self.file_object = pfile_io.TarFileIO(extracted_file_object)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    stats_object = pstats.Stats()
    stats_object.fs_type = 'Tar container'
    self._stat = stats_object
    return stats_object


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
    self._fs = None

  def _OpenFileSystem(self, path, offset):
    """Open the filesystem object and store a copy of it for caching.

    Args:
      path: Path to the image file.
      offset: If this is a disk partition an offset to the filesystem
      is needed.

    Raises:
      IOError: If no pfile.FilesystemCache object is provided.
    """
    if not hasattr(self, '_fscache'):
      raise IOError('No FS cache provided, unable to open a file.')

    fs_obj = self._fscache.Open(path, offset)
    self._fs = fs_obj.fs

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
      path = file_entry
    else:
      path = self.pathspec.container_path

    image_offset = getattr(self.pathspec, 'image_offset', 0)
    self._OpenFileSystem(path, image_offset)

    inode = getattr(self.pathspec, 'image_inode', 0)

    if not hasattr(self.pathspec, 'file_path'):
      self.pathspec.file_path = 'NA_NotProvided'

    self.file_object = pfile_io.TSKFileIO(
        self._fs, inode, self.pathspec.file_path)

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
    if getattr(self, '_stat', None):
      return self._stat

    stats_object = pstats.Stats()

    try:
      info = self.file_object.fileobj.info
      meta = info.meta
    except IOError:
      return stats_object

    if not meta:
      return stats_object

    fs_type = ''
    stats_object.mode = getattr(meta, 'mode', None)
    stats_object.ino = getattr(meta, 'addr', None)
    stats_object.nlink = getattr(meta, 'nlink', None)
    stats_object.uid = getattr(meta, 'uid', None)
    stats_object.gid = getattr(meta, 'gid', None)
    stats_object.size = getattr(meta, 'size', None)
    stats_object.atime = getattr(meta, 'atime', None)
    stats_object.atime_nano = getattr(meta, 'atime_nano', None)
    stats_object.crtime = getattr(meta, 'crtime', None)
    stats_object.crtime_nano = getattr(meta, 'crtime_nano', None)
    stats_object.mtime = getattr(meta, 'mtime', None)
    stats_object.mtime_nano = getattr(meta, 'mtime_nano', None)
    stats_object.ctime = getattr(meta, 'ctime', None)
    stats_object.ctime_nano = getattr(meta, 'ctime_nano', None)
    stats_object.dtime = getattr(meta, 'dtime', None)
    stats_object.dtime_nano = getattr(meta, 'dtime_nano', None)
    stats_object.bkup_time = getattr(meta, 'bktime', None)
    stats_object.bkup_time_nano = getattr(meta, 'bktime_nano', None)
    fs_type = str(self._fs.info.ftype)

    flags = getattr(meta, 'flags', 0)

    # The flags are an instance of pytsk3.TSK_FS_META_FLAG_ENUM.
    if int(flags) & pytsk3.TSK_FS_META_FLAG_ALLOC:
      stats_object.allocated = True
    else:
      stats_object.allocated = False

    if fs_type.startswith('TSK_FS_TYPE'):
      stats_object.fs_type = fs_type[12:]
    else:
      stats_object.fs_type = fs_type

    self._stat = stats_object
    return stats_object


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

  def _OpenFileSystem(self, path, offset):
    """Open a filesystem object for a VSS file."""
    if not hasattr(self.pathspec, 'vss_store_number'):
      raise IOError((u'Unable to open VSS file: {%s} -> No VSS store number '
                     'defined.') % self.name)

    if not hasattr(self, '_fscache'):
      raise IOError('No FS cache provided, unable to contine.')

    self._fs_obj = self._fscache.Open(
        path, offset, self.pathspec.vss_store_number)

    self._fs = self._fs_obj.fs

  def Open(self, file_entry=None):
    """Open the file as it is described in the PathSpec protobuf.

    Args:
      file_entry: Optional parent file entry object. The default is None.

    Returns:
      A file-like object.
    """
    file_object = super(VssFileEntry, self).Open(file_entry=file_entry)

    self.display_name = u'%s:vss_store_%d' % (
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
      raise IOError(u'Unable to open ZIP file: {%s} -> %s' % (self.name, e))

    self.file_object = pfile_io.ZipFileIO(
        zip_file, self.pathspec.file_path, self.zipinfo.file_size)
    return self.file_object

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    stats_object = pstats.Stats()

    # TODO: Make this a proper stat element with as much information
    # as can be extracted.
    # Also confirm for sure that this is the correct timestamp and it is
    # stored in UTC (or if it is in local timezone, adjust it)
    stats_object.ctime = timelib.Timetuple2Timestamp(self.zipinfo.date_time)
    stats_object.size = self.zipinfo.file_size
    stats_object.fs_type = 'ZIP Container'

    self._stat = stats_object
    return stats_object
