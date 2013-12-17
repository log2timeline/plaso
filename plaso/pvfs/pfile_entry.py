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

import bz2
import gzip
import os
import tarfile
import zipfile

from plaso.lib import errors
from plaso.lib import registry
from plaso.lib import sleuthkit
from plaso.lib import timelib
from plaso.pvfs import pstats


class PlasoFileEntry(object):
  """Base class for a file entry object."""
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  TYPE = 'UNSET'

  def __init__(self, proto, root=None, fscache=None):
    """Constructor.

    Args:
      proto: The transmission_proto that describes the file.
      root: The root transmission_proto that describes the file if one exists.
      fscache: A FilesystemCache object.

    Raises:
      errors.UnableToOpenFile: If this class supports the wrong driver for this
      file.
    """
    super(PlasoFileEntry, self).__init__()
    self.pathspec = proto
    if root:
      self.pathspec_root = root
    else:
      self.pathspec_root = proto
    self.name = ''

    if fscache:
      self._fscache = fscache

    if proto.type != self.TYPE:
      raise errors.UnableToOpenFile('Unable to handle this file type.')

    self._stat = None

  def __enter__(self):
    """Make it work with the with statement."""
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    """Make it work with the with statement."""
    _ = exc_type
    _ = exc_value
    _ = traceback
    self.close()
    return False

  def __str__(self):
    """Return a string representation of the file object, the display name."""
    if hasattr(self, 'display_name'):
      return self.display_name
    else:
      return 'Unknown File'

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf.

    This method reads the content of the PathSpec protobuf and opens
    the filehandle up according to the driver the class supports.

    Filehandle can be passed to the method if the file that needs to
    be opened is within another file.

    Args:
      filehandle: A PlasoFile object that the file is contained within.
    """
    raise NotImplementedError

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    raise NotImplementedError

  def HasParent(self):
    """Check if the PathSpec defines a parent."""
    return hasattr(self.pathspec, 'nested_pathspec')


class TskFileEntry(PlasoFileEntry):
  """Class to open up files using TSK."""

  TYPE = 'TSK'

  def __init__(self, fscache):
    """Constructor."""
    super(TskFileEntry, self).__init__()
    self.fh = None
    self._fs = None
    self._fscache = fscache
    self._stat = None

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

    self.fh = None
    self._fs = fs_obj.fs

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()
    if not self.fh:
      return ret

    try:
      info = self.fh.fileobj.info
      meta = info.meta
    except IOError:
      return ret

    if not meta:
      return ret

    fs_type = ''
    ret.mode = getattr(meta, 'mode', None)
    ret.ino = getattr(meta, 'addr', None)
    ret.nlink = getattr(meta, 'nlink', None)
    ret.uid = getattr(meta, 'uid', None)
    ret.gid = getattr(meta, 'gid', None)
    ret.size = getattr(meta, 'size', None)
    ret.atime = getattr(meta, 'atime', None)
    ret.atime_nano = getattr(meta, 'atime_nano', None)
    ret.crtime = getattr(meta, 'crtime', None)
    ret.crtime_nano = getattr(meta, 'crtime_nano', None)
    ret.mtime = getattr(meta, 'mtime', None)
    ret.mtime_nano = getattr(meta, 'mtime_nano', None)
    ret.ctime = getattr(meta, 'ctime', None)
    ret.ctime_nano = getattr(meta, 'ctime_nano', None)
    ret.dtime = getattr(meta, 'dtime', None)
    ret.dtime_nano = getattr(meta, 'dtime_nano', None)
    ret.bkup_time = getattr(meta, 'bktime', None)
    ret.bkup_time_nano = getattr(meta, 'bktime_nano', None)
    fs_type = str(self._fs.info.ftype)

    check_allocated = getattr(self.fh.fileobj, 'IsAllocated', None)
    if check_allocated:
      ret.allocated = check_allocated()
    else:
      ret.allocated = True

    if fs_type.startswith('TSK_FS_TYPE'):
      ret.fs_type = fs_type[12:]
    else:
      ret.fs_type = fs_type

    self._stat = ret
    return ret

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf.

    This method reads the content of the PathSpec protobuf and opens
    the filehandle using the Sleuthkit (TSK).

    Args:
      filehandle: A PlasoFile object that the file is contained within.
    """
    if filehandle:
      path = filehandle
    else:
      path = self.pathspec.container_path

    if hasattr(self.pathspec, 'image_offset'):
      self._OpenFileSystem(path, self.pathspec.image_offset)
    else:
      self._OpenFileSystem(path, 0)

    inode = 0
    if hasattr(self.pathspec, 'image_inode'):
      inode = self.pathspec.image_inode

    if not hasattr(self.pathspec, 'file_path'):
      self.pathspec.file_path = 'NA_NotProvided'

    self.fh = sleuthkit.Open(
        self._fs, inode, self.pathspec.file_path)

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    self.size = self.fh.size
    self.display_name = u'{}:{}{}'.format(
        self.pathspec.container_path, path_prepend,
        self.pathspec.file_path)
    if filehandle:
      self.display_name = u'{}:{}{}'.format(
          filehandle.name, path_prepend, self.display_name)


class OsFileEntry(PlasoFileEntry):
  """Class to provide a file-like object to a file stored on a filesystem."""

  TYPE = 'OS'

  def __init__(self):
    """Constructor."""
    super(OsFileEntry, self).__init__()
    self.fh = None
    self.name = None
    self._stat = None

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf."""
    self.fh = open(self.pathspec.file_path, 'rb')
    self.name = self.pathspec.file_path
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if filehandle:
      self.display_name = u'{}:{}{}'.format(
          filehandle.name, path_prepend, self.name)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.name)

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()
    if not self.fh:
      return ret

    stat = os.stat(self.name)
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

    self._stat = ret
    return ret


class ZipFileEntry(PlasoFileEntry):
  """Provide a file-like object to a file stored inside a ZIP file."""
  TYPE = 'ZIP'

  def __init__(self):
    """Constructor."""
    super(ZipFileEntry, self).__init__()

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()

    if not self.fh:
      return ret

    # TODO: Make this a proper stat element with as much information
    # as can be extracted.
    # Also confirm for sure that this is the correct timestamp and it is
    # stored in UTC (or if it is in local timezone, adjust it)
    ret.ctime = timelib.Timetuple2Timestamp(self.zipinfo.date_time)
    ret.ino = self.inode
    ret.size = self.zipinfo.file_size
    ret.fs_type = 'ZIP Container'

    self._stat = ret
    return ret

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf."""
    if filehandle:
      try:
        zf = zipfile.ZipFile(filehandle, 'r')
      except zipfile.BadZipfile as e:
        raise IOError(
            u'Unable to open ZIP file, not a ZIP file?: {} [{}]'.format(
                filehandle.name, e))
      path_name = filehandle.name
      self.inode = getattr(filehandle.Stat(), 'ino', 0)
    else:
      path_name = self.pathspec.container_path
      zf = zipfile.ZipFile(path_name, 'r')
      self.inode = os.stat(path_name).st_ino

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    if filehandle:
      self.display_name = u'{}:{}{}'.format(
          filehandle.display_name, path_prepend, self.pathspec.file_path)
    else:
      self.display_name = u'{}:{}{}'.format(
          path_name, path_prepend, self.pathspec.file_path)
    self.offset = 0
    self.orig_fh = filehandle
    self.zipinfo = zf.getinfo(self.pathspec.file_path)
    self.size = self.zipinfo.file_size
    try:
      self.fh = zf.open(self.pathspec.file_path, 'r')
    except (RuntimeError, zipfile.BadZipfile) as e:
      raise IOError(u'Unable to open ZIP file: {%s} -> %s' % (self.name, e))


class GzipFileEntry(PlasoFileEntry):
  """Provide a file-like object to a file compressed using GZIP."""
  TYPE = 'GZIP'

  def __init__(self):
    """Constructor."""
    super(GzipFileEntry, self).__init__()

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()
    if not self.fh:
      return ret

    ret.size = self.size
    ret.ino = self.inode
    ret.fs_type = 'GZ File'

    self._stat = ret
    return ret

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf."""
    if filehandle:
      filehandle.seek(0)
      self.fh = gzip.GzipFile(fileobj=filehandle, mode='rb')
      self.inode = getattr(filehandle.Stat(), 'ino', 0)
    else:
      self.fh = gzip.GzipFile(filename=self.pathspec.file_path, mode='rb')
      self.inode = os.stat(self.pathspec.file_path).st_ino

    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    if filehandle:
      self.display_name = u'{}{}_uncompressed'.format(
          path_prepend, filehandle.name)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.name)

    # To get the size properly calculated.
    try:
      _ = self.fh.read(4)
    except IOError as e:
      dn = self.display_name
      raise IOError('Not able to open the GZIP file %s -> %s [%s]' % (
          self.name, dn, e))
    self.fh.rewind()
    try:
      self.size = self.fh.size
    except AttributeError:
      self.size = 0


class Bz2FileEntry(PlasoFileEntry):
  """Provide a file-like object to a file compressed using BZ2."""
  TYPE = 'BZ2'

  def __init__(self):
    """Constructor."""
    super(Bz2FileEntry, self).__init__()

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()
    if not self.fh:
      return ret

    ret.ino = self.inode
    ret.fs_type = 'BZ2 container'
    self._stat = ret
    return ret

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf."""
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if filehandle:
      self.inode = getattr(filehandle.Stat(), 'ino', 0)
      try:
        filehandle.seek(0)
      except NotImplementedError:
        pass
      self.fh = bz2.BZ2File(filehandle, 'r')
      self.display_name = u'{}:{}{}'.format(
          filehandle.name, path_prepend, self.pathspec.file_path)
    else:
      self.display_name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
      self.fh = bz2.BZ2File(self.pathspec.file_path, 'r')
      self.inode = os.stat(self.pathspec.file_path).st_ino

    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)


class TarFileEntry(PlasoFileEntry):
  """Provide a file-like object to a file stored inside a TAR file."""
  TYPE = 'TAR'

  def __init__(self):
    """Constructor."""
    super(TarFileEntry, self).__init__()

  def Stat(self):
    """Return a Stats object that contains stats like information."""
    if getattr(self, '_stat', None):
      return self._stat

    ret = pstats.Stats()
    if not self.fh:
      return ret

    ret.ino = self.inode
    ret.fs_type = 'Tar container'
    self._stat = ret
    return ret

  def Open(self, filehandle=None):
    """Open the file as it is described in the PathSpec protobuf."""
    path_prepend = getattr(self.pathspec, 'path_prepend', '')
    if filehandle:
      ft = tarfile.open(fileobj=filehandle, mode='r')
      self.display_name = u'{}:{}{}'.format(
          filehandle.name, path_prepend, self.pathspec.file_path)
      self.inode = getattr(filehandle.Stat(), 'ino', 0)
    else:
      self.display_name = u'{}:{}{}'.format(
          self.pathspec.container_path, path_prepend,
          self.pathspec.file_path)
      ft = tarfile.open(self.pathspec.container_path, 'r')
      self.inode = os.stat(self.pathspec.container_path).st_ino

    self.fh = ft.extractfile(self.pathspec.file_path)
    if not self.fh:
      raise IOError(
          u'[TAR] File %s empty or unable to open.' % self.pathspec.file_path)
    self.buffer = ''
    self.name = u'{}{}'.format(path_prepend, self.pathspec.file_path)
    self.size = self.fh.size


class VssFileEntry(TskFileEntry):
  """Class to open up files in Volume Shadow Copies."""

  TYPE = 'VSS'

  def __init__(self):
    """Constructor."""
    super(VssFileEntry, self).__init__()

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

  def Open(self, filehandle=None):
    """Open a VSS file, which is a subset of a TSK file."""
    super(VssFileEntry, self).Open(filehandle)

    self.display_name = u'%s:vss_store_%d' % (
        self.display_name, self.pathspec.vss_store_number)
