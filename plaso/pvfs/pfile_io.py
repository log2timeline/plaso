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
"""File for PyVFS migration to contain IO related functionality."""

import abc
import logging
import os
import zlib
import zipfile

import pytsk3


class BaseFileIO(object):
  """Base class for a file-like object."""

  def __init__(self):
    """Initializes the file-like object."""
    super(BaseFileIO, self).__init__()

  def __iter__(self):
    """Returns a generator that returns all the lines in the file."""
    line = self.readline()
    while line:
      yield line
      line = self.readline()

  # Implementing an interface.
  @abc.abstractmethod
  def close(self):
    """Closes the file."""

  # Implementing an interface.
  def fileno(self):
    """Return the integer file descriptor if possible.

    This function should not be defined by any file like object
    unless it really can return a reliable file descriptor. That is
    by nature not really possible when dealing with files inside
    containers such as image files or compressed archives. However
    some parsers specifically require this function to be implemented
    despite never really using it.

    Returns:
      An integer file descriptor if possible, -1 otherwise.
    """
    return getattr(self._file_object, 'fileno', -1)

  # Implementing an interface.
  @abc.abstractmethod
  def read(self, size=None):
    """Read size bytes from file and return them."""

  # Implementing an interface.
  @abc.abstractmethod
  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """

  # Implementing an interface.
  @abc.abstractmethod
  def seek(self, offset, whence=os.SEEK_SET):
    """Seek to an offset in the file."""

  # Implementing an interface.
  @abc.abstractmethod
  def tell(self):
    """Return the current offset into the file."""

  def get_offset(self):
    """Returns the current offset."""
    return self.tell()

  # Implementing an interface.
  @abc.abstractmethod
  def get_size(self):
    """Returns the file size."""


class Bz2FileIO(BaseFileIO):
  """Provide a file-like object to a file compressed using BZ2."""

  def __init__(self, bzip2_file):
    """Initializes the file-like object.

    Args:
      bzip2_file: the bzip2 file object.
    """
    super(Bz2FileIO, self).__init__()
    self._bzip2_file = bzip2_file

  def close(self):
    """Closes the file."""
    if self._bzip2_file:
      self._bzip2_file.close()
      self._bzip2_file = None

  def read(self, size=None):
    """Read size bytes from file and return them."""
    return self._bzip2_file.read(size)

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if size is None:
      size = -1
    return self._bzip2_file.readline(size)

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek to an offset in the file."""
    self._bzip2_file.seek(offset, whence)

  def tell(self):
    """Return the current offset into the file."""
    return self._bzip2_file.tell()

  def get_size(self):
    """Returns the file size."""
    # TODO: implement if necessary.
    return -1L


class GzipFileIO(BaseFileIO):
  """Provide a file-like object to a file compressed using GZIP."""

  def __init__(self, gzip_file):
    """Initializes the file-like object.

    Args:
      gzip_file: the gzip file object.
    """
    super(GzipFileIO, self).__init__()
    self._gzip_file = gzip_file

  def close(self):
    """Closes the file."""
    if self._gzip_file:
      self._gzip_file.close()
      self._gzip_file = None

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if size is None:
      size = -1
    return self._gzip_file.read(size)

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    return self._gzip_file.readline(size)

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek into a specific location in a file.

    This method implements a simple method to seek into a
    compressed file from the end, which is not implemented by the
    gzip library.

    Args:
      offset: An integer, indicating the number of bytes to seek in file,
      how that value is interpreted depends on the 'whence' value.
      whence: An integer; 0 means from beginning, 1 from last position
      and 2 indicates we are about to seek from the end of the file.

    Raises:
      RuntimeError: If a seek is attempted to a closed file.
    """
    if not self._gzip_file:
      raise RuntimeError('Unable to seek into a file that is not open.')

    if whence == 2:
      ofs = self._gzip_file.size + offset
      if ofs > self._gzip_file.tell():
        self._gzip_file.seek(ofs - self._gzip_file.offset, 1)
      else:
        self._gzip_file.rewind()
        self._gzip_file.seek(ofs)
    else:
      self._gzip_file.seek(offset, whence)

  def tell(self):
    """Return the current offset into the file."""
    return self._gzip_file.tell()

  def get_size(self):
    """Returns the file size."""
    return long(self._gzip_file.size)


class OsFileIO(BaseFileIO):
  """Class to provide a file-like object to a file stored on a filesystem."""

  def __init__(self, file_object, size):
    """Initializes the file-like object.

    Args:
      file_object: the os file-like object.
      size: the in-ZIP file size.
    """
    super(OsFileIO, self).__init__()
    self._file_object = file_object
    self._size = size

  def close(self):
    """Closes the file."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if size is None:
      size = -1
    return self._file_object.read(size)

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if size is None:
      size = -1
    return self._file_object.readline(size)

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek to an offset in the file."""
    self._file_object.seek(offset, whence)

  def tell(self):
    """Return the current offset into the file."""
    return self._file_object.tell()

  def get_size(self):
    """Returns the file size."""
    return long(self._size)


class TarFileIO(BaseFileIO):
  """Provide a file-like object to a file stored inside a TAR file."""

  def __init__(self, extracted_file_object):
    """Initializes the file-like object.

    Args:
      extracted_file_object: the extracted file object.
    """
    super(TarFileIO, self).__init__()
    self._extracted_file_object = extracted_file_object
    self.buffer = ''

  def close(self):
    """Closes the file."""
    if self._extracted_file_object:
      self._extracted_file_object.close()
      self._extracted_file_object = None

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if not self._extracted_file_object:
      return ''

    if size and len(self.buffer) >= size:
      ret = self.buffer[:size]
      self.buffer = self.buffer[size:]
      return ret

    ret = self.buffer
    self.buffer = ''

    read_size = None
    if size:
      read_size = size - len(ret)

    ret += self._extracted_file_object.read(read_size)

    # In my testing I've seen the underlying read operation
    # sometimes read in way more than the size here indicates.
    # Slapping an additional check to make sure we return the amount
    # of bytes that we are really asking for.
    if size and len(ret) > size:
      self.buffer = ret[size:]
      ret = ret[:size]

    return ret

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if size is None:
      size = -1
    if not self._extracted_file_object:
      return ''

    if '\n' not in self.buffer:
      self.buffer += self._extracted_file_object.readline(size)

    # TODO: Make this more resiliant/optimized. For now this
    # code only checks the size in two places, better to always fill
    # the buffer, make sure it is of certain size before moving on.
    if size > 0 and len(self.buffer) > size:
      ret = self.buffer[:size]
      self.buffer = self.buffer[size:]
    else:
      ret = self.buffer
      self.buffer = ''

    result, sep, ret = ret.partition('\n')
    self.buffer = ret + self.buffer

    return result + sep

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek into the file-like object."""
    if not self._extracted_file_object:
      raise RuntimeError('Unable to seek into a file that is not open.')

    if whence == 1:
      if offset > 0 and len(self.buffer) > offset:
        self.buffer = self.buffer[offset:]
      else:
        ofs = offset - len(self.buffer)
        self.buffer = ''
        self._extracted_file_object.seek(ofs, 1)
    else:
      self.buffer = ''
      self._extracted_file_object.seek(offset, whence)

  def tell(self):
    """Return the current offset of the file-like object."""
    return self._extracted_file_object.tell() - len(self.buffer)

  def get_size(self):
    """Returns the file size."""
    # TODO: implement if necessary.
    return -1L


class TSKFileIO(BaseFileIO):
  """Class that simulates most of the methods of a read-only file object."""
  MIN_READSIZE = 1024 * 1024

  def __init__(self, filesystem, inode, path):
    """Constructor for the TSKFile class.

    This class assumes that a filesystem using pytsk3.FS_Info has already been
    created.

    The file object that is returned can be used in most basic ways like a
    normal file object, that is the read methods. No write support is
    implemented, since the intention of this class is to provide a read-only
    interface to raw disk images.

    Args:
      filesystem: A pytsk3.FS_Info filesystem object.
      inode: An inode number for the the file.
      path: Full name (with path) of the file being opened.

    Raises:
      IOError: if the file opened does not have a metadata structure available
      or if this is a directory object instead of a file one.
    """
    super(TSKFileIO, self).__init__()
    self.inode = inode
    self.tsk_fs = filesystem

    # We prefer opening up a file by it's inode number since its faster.
    if inode:
      self.fileobj = self.tsk_fs.open_meta(inode=inode)
    else:
      self.fileobj = self.tsk_fs.open(path)

    self.size = self.fileobj.info.meta.size
    self.name = path
    self.ctime = self.fileobj.info.meta.ctime

    if not self.fileobj.info.meta:
      raise IOError('No valid metastructure for inode: %d' % inode)

    self.readahead = ''
    self.next_read_offset = 0

  def close(self):
    """Closes the file."""
    return

  # Deviate from the naming convention since we are implementing an interface.
  def read(self, read_size=None):
    """Provide a read method for the file object.

    Args:
      read_size: An integer indicating the number of bytes to read.

    Returns:
      The content from the file, from the current offset and for read_size
      bytes.

    Raises:
      IOError: if no read_size is passed on.
    """
    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot read from directory.')

    if read_size is None:
      # Check file size and read within "reasonable" limits.
      if self.size - self.tell() < 1024 * 1024 * 24:
        read_size = self.size - self.tell()
      else:
        read_size = 1024 * 1024 * 24
        logging.debug(('Trying to read unbound size. Read size limited to the'
                       'maximum size of 24Mb . Size of file: %d, and current'
                       ' position in it: %d'), self.size, self.tell())

    if read_size <= len(self.readahead):
      data = self.readahead[:read_size]
      self.readahead = self.readahead[read_size:]
    else:
      data = self.readahead
      self.readahead = ''
      read_size -= len(data)
      read_now_size = min(self.size - self.tell(),
                          read_size + self.MIN_READSIZE)
      if read_now_size < 0:
        return data
      try:
        buf = self.fileobj.read_random(self.next_read_offset, read_now_size)
        self.next_read_offset += len(buf)
        self.readahead = buf[read_size:]
        data += buf[:read_size]
      except IOError:
        return data

    return data

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot read from directory.')

    read_size = size or self.MIN_READSIZE

    # check if we need to read more into the buffer
    if '\n' not in self.readahead and read_size >= len(self.readahead):
      self.readahead = self.read(read_size)

    result, sep, self.readahead = self.readahead.partition('\n')

    return result + sep

  def seek(self, offset, whence=0):
    """Implement a seek method.

    Set the file's current position.

    Args:
      offset: The offset to where the current position should be.
      whence: Defines whether offset is an absolute or relative
      position into the file or if it is relative to the end of the
      file.

    Raises:
      IOError:
    """
    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot seek in directory.')

    # TODO: Buffering needs to be properly fixed. The current
    # solution is to keep the buffer somewhat between seek operations
    # but it can be improved even further. Buffering should also be
    # a generic buffering, not specifically designed for TSK operations.
    # And the seek function should not need to worry about the buffer
    # at all, that should be moved to other layers, put in here as a
    # temporary solution until PyVFS gets completed.
    if whence == os.SEEK_CUR:
      if offset > len(self.readahead):
        self.readahead = ''
        self.next_read_offset = self.tell() + offset
      elif offset < 0:
        self.readahead = ''
        self.next_read_offset = self.tell() + offset
      else:
        self.readahead = self.readahead[offset:]
    elif whence == os.SEEK_END:
      self.next_read_offset = self.size + offset
      self.readahead = ''
    elif whence == os.SEEK_SET:
      lower = self.tell()
      upper = self.next_read_offset
      if offset < lower or offset > upper:
        self.readahead = ''
        self.next_read_offset = offset
      elif offset == lower:
        pass
      else:
        self.readahead = self.readahead[offset - lower:]
    else:
      raise IOError('Invalid argument for whence.')

    if self.next_read_offset < 0:
      raise IOError('Offset cannot be less than zero.')

  def tell(self):
    """Return the current offset into the file."""
    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot retrieve offset form directory.')

    return self.next_read_offset - len(self.readahead)

  def get_size(self):
    """Returns the file size."""
    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot retrieve size form directory.')

    size = getattr(self.fileobj.info.meta, 'size', 0)
    return long(size)

  # TODO: this is different from the rest of the pfile objects.

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.close()

  def isatty(self):
    """Return a bool indicating if the file is connected to tty-like device."""
    return False

  def readlines(self, sizehint=None):
    """Read until EOF using readline() unless sizehint is provided.

    Args:
      sizehint: Read whole lines until either EOF or number of bytes
      as defined in sizehint are reached.

    Yields:
      A list of lines.
    """
    if sizehint is None or sizehint <= 0:
      sizehint = self.MIN_READSIZE

    while sizehint > 0:
      line = self.readline(sizehint)
      if not line:
        break
      yield line
      sizehint -= len(line)


class ZipFileIO(BaseFileIO):
  """Provide a file-like object to a file stored inside a ZIP file."""

  def __init__(self, zip_file, file_path, size):
    """Initializes the file-like object.

    Args:
      zip_file: the ZIP file object.
      file_path: the in-ZIP file path.
      size: the in-ZIP file size.
    """
    super(ZipFileIO, self).__init__()
    self._zip_file = zip_file
    self._file_path = file_path
    self._size = size
    self._extracted_file_object = None
    self.offset = 0

  def close(self):
    """Closes the file."""
    if self._extracted_file_object:
      self._extracted_file_object.close()
      self._extracted_file_object = None
    self.offset = 0

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if self.offset >= self._size:
      return ''

    if not self._extracted_file_object:
      try:
        self._extracted_file_object = self._zip_file.open(self._file_path, 'r')
      except (RuntimeError, zipfile.BadZipfile) as e:
        raise IOError(u'Unable to open ZIP file with error: %s' % e)
      self.offset = 0

    # There is an error in the ZipExtFile, at least with Python v 2.6.
    # If a readline is called the results are stored in linebuffer,
    # while read uses the readbuffer for buffer, ignoring the content
    # of linebuffer.
    if hasattr(self._extracted_file_object, 'linebuffer'):
      if self._extracted_file_object.linebuffer:
        self._extracted_file_object.readbuffer = (
            self._extracted_file_object.linebuffer +
            self._extracted_file_object.readbuffer)
        self._extracted_file_object.linebuffer = ''

    if size is None:
      size = min(self._size - self.offset, 1024 * 1024 * 24)
      logging.debug(u'[ZIP] Unbound read attempted: %s -> %s', self.name,
                    self.display_name)
      if size != self._size - self.offset:
        logging.debug('[ZIP] Not able to read in the entire file (too large).')

    try:
      line = self._extracted_file_object.read(size)
    except zlib.error:
      raise IOError

    self.offset += len(line)
    return line

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if self.offset >= self._size:
      return ''

    if not self._extracted_file_object:
      try:
        self._extracted_file_object = self._zip_file.open(self._file_path, 'r')
      except (RuntimeError, zipfile.BadZipfile) as e:
        raise IOError(u'Unable to open ZIP file with error: %s' % e)
      self.offset = 0

    line = self._extracted_file_object.readline(size)
    self.offset += len(line)
    return line

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek into the file."""
    if whence == os.SEEK_CUR:
      offset += self.offset

    elif whence == os.SEEK_END:
      offset = self._size + offset

    elif whence != os.SEEK_SET:
      raise RuntimeError('Invalid whence: %d' % whence)

    if offset < 0:
      raise RuntimeError('Invalid offset: %d' % offset)

    if offset >= self._size:
      return

    if offset < self.offset:
      self._extracted_file_object.close()
      self._extracted_file_object = None
      read_size = offset
    else:
      read_size = offset - self.offset

    if not self._extracted_file_object:
      try:
        self._extracted_file_object = self._zip_file.open(self._file_path, 'r')
      except (RuntimeError, zipfile.BadZipfile) as e:
        raise IOError(u'Unable to open ZIP file with error: %s' % e)
      self.offset = 0

    _ = self._extracted_file_object.read(read_size)
    self.offset += read_size

  def tell(self):
    """Return the current offset into the file.

    A ZipExtFile object maintains an object called fileobj that implements
    a tell function, which reads the offset into the current fileobj.

    However, that object may have some data that has been read in that is
    stored in buffers, so we need to subtract buffer read data to get the
    actual offset into the file.

    Returns:
      An offset into the file, indicating current location.
    """
    return self.offset

  def get_size(self):
    """Returns the file size."""
    return long(self._size)
