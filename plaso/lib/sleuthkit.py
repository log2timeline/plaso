#!/usr/bin/python
#
# -*- coding: utf-8 -*-
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
"""This file contains a class to provide a read only fileobject from TSK.

This class provides a method to create a filehandle from an image file
that is readable by TSK (Sleuthkit) and use like an ordinary file in Python.
"""
import os
import logging
import platform

import pytsk3


def Open(fs, inode, name):
  """Shorthand for TSKFile(fs, inode, path).

  Args:
    fs: An FS_Info object from PyTSK3
    inode: The inode number of the file needed to be read.
    name: The full path to the file inside the image.
  Returns:
    A filehandle that can be used by Python.
  """
  return TSKFile(fs, inode, name)


class TSKFile(object):
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
    self.inode = inode
    self.fs = filesystem

    # We prefer opening up a file by it's inode number since its faster.
    if inode:
      self.fileobj = self.fs.open_meta(inode=inode)
    # Ignore a leading path separator: \ on Windows.
    # This prevents the cannot access \$MFT issue.
    # TODO: this is a workaround for now and needs to be fixed in pyvfs.
    elif platform.system() == 'Windows' and path.startswith('\\'):
      self.fileobj = self.fs.open(path[1:])
    else:
      self.fileobj = self.fs.open(path)

    self.size = self.fileobj.info.meta.size
    self.name = path
    self.ctime = self.fileobj.info.meta.ctime

    if not self.fileobj.info.meta:
      raise IOError('No valid metastructure for inode: %d' % inode)

    if self.fileobj.info.meta.type != pytsk3.TSK_FS_META_TYPE_REG:
      raise IOError('Cannot open a directory.')

    self.readahead = ''
    self.next_read_offset = 0

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

  def IsAllocated(self):
    """Return a boolean indicating if the file is allocated or not."""
    ret = False
    flags = self.fileobj.info.meta.flags

    if flags:
      if int(flags) & int(pytsk3.TSK_FS_META_FLAG_ALLOC):
        ret = True

    return ret

  def close(self):
    """Close the file."""
    return

  def isatty(self):
    """Return a bool indicating if the file is connected to tty-like device."""
    return False

  def tell(self):
    """Return the current offset into the file."""
    return self.next_read_offset - len(self.readahead)

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

  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    read_size = size or self.MIN_READSIZE

    # check if we need to read more into the buffer
    if '\n' not in self.readahead and read_size >= len(self.readahead):
      self.readahead = self.read(read_size)

    result, sep, self.readahead = self.readahead.partition('\n')

    return result + sep

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

  def __iter__(self):
    """Return a generator that returns all the lines in the file."""
    while 1:
      line = self.readline()
      if not line:
        break
      yield line

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


