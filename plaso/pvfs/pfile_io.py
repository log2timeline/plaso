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

import logging
import zlib


class PlasoFileIO(object):
  """Base class for a file-like object."""

  def __init__(self, fh):
    """Constructor."""
    super(PlasoFileIO, self).__init__()
    self.fh = fh

  # Implementing an interface.
  def seek(self, offset, whence=0):
    """Seek to an offset in the file."""
    if self.fh:
      self.fh.seek(offset, whence)
    else:
      raise RuntimeError('Unable to seek into a file that is not open.')

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
    if not self.fh:
      return -1

    return getattr(self.fh, 'fileno', -1)

  # Implementing an interface.
  def read(self, size=None):
    """Read size bytes from file and return them."""
    if self.fh:
      # Some internal implementations require unbound read operations
      # to use a -1 as the default value, others None.
      try:
        return self.fh.read(size)
      except TypeError:
        return self.fh.read(-1)
    else:
      return ''

  # Implementing an interface.
  def tell(self):
    """Return the current offset into the file."""
    if self.fh:
      return self.fh.tell()
    else:
      return 0

  # Implementing an interface.
  def close(self):
    """Close the file."""
    if self.fh:
      self.fh.close()
      self.fh = None

  # Implementing an interface.
  def readline(self, size=None):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if self.fh:
      return self.fh.readline(size)
    else:
      return ''

  def __iter__(self):
    """Implement an iterator that reads each line."""
    line = self.readline()
    while line:
      yield line
      line = self.readline()


class OsFileIO(PlasoFileIO):
  """Class to provide a file-like object to a file stored on a filesystem."""

  def __init__(self, fh):
    """Constructor."""
    super(OsFileIO, self).__init__(fh)

  def readline(self, size=-1):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if self.fh:
      return self.fh.readline(size)
    else:
      return ''


class ZipFileIO(PlasoFileIO):
  """Provide a file-like object to a file stored inside a ZIP file."""

  def __init__(self, fh):
    """Constructor."""
    super(ZipFileIO, self).__init__(fh)

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if not self.fh:
      return ''

    # There is an error in the ZipExtFile, at least with Python v 2.6.
    # If a readline is called the results are stored in linebuffer,
    # while read uses the readbuffer for buffer, ignoring the content
    # of linebuffer.
    if hasattr(self.fh, 'linebuffer'):
      if self.fh.linebuffer:
        self.fh.readbuffer = self.fh.linebuffer + self.fh.readbuffer
        self.fh.linebuffer = ''

    if size is None:
      size = min(self.size - self.offset, 1024 * 1024 * 24)
      logging.debug(u'[ZIP] Unbound read attempted: %s -> %s', self.name,
                    self.display_name)
      if size != self.size - self.offset:
        logging.debug('[ZIP] Not able to read in the entire file (too large).')

    try:
      line = self.fh.read(size)
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
    if self.fh:
      line = self.fh.readline(size)
      self.offset += len(line)
      return line
    else:
      return ''

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
    if not self.fh:
      return 0

    return self.offset

  def close(self):
    """Close the file."""
    if self.fh:
      self.fh.close()
      self.fh = None
      self.offset = 0

  def seek(self, offset, whence=0):
    """Seek into the file."""
    if not self.fh:
      raise RuntimeError('Unable to seek into a file that is not open.')

    if whence == 0:
      self.close()
      self.Open(self.orig_fh)
      _ = self.read(offset)
    elif whence == 1:
      if offset > 0:
        _ = self.read(offset)
      else:
        ofs = self.offset + offset
        self.seek(ofs)
    elif whence == 2:
      ofs = self.size + offset
      if ofs > self.offset:
        _ = self.read(ofs - self.offset)
      else:
        self.seek(0)
        _ = self.read(ofs)
    else:
      raise RuntimeError('Illegal whence value %s' % whence)


class GzipFileIO(PlasoFileIO):
  """Provide a file-like object to a file compressed using GZIP."""

  def __init__(self, fh):
    """Constructor."""
    super(GzipFileIO, self).__init__(fh)

  def seek(self, offset, whence=0):
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
    if not self.fh:
      raise RuntimeError('Unable to seek into a file that is not open.')

    if whence == 2:
      ofs = self.size + offset
      if ofs > self.tell():
        self.fh.seek(ofs - self.fh.offset, 1)
      else:
        self.fh.rewind()
        self.fh.seek(ofs)
    else:
      self.fh.seek(offset, whence)

  def read(self, size=-1):
    """Read size bytes from file and return them."""
    if self.fh:
      return self.fh.read(size)
    else:
      return ''


class Bz2FileIO(PlasoFileIO):
  """Provide a file-like object to a file compressed using BZ2."""

  def __init__(self, fh):
    """Constructor."""
    super(Bz2FileIO, self).__init__(fh)

  def readline(self, size=-1):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if self.fh:
      return self.fh.readline(size)
    else:
      return ''


class TarFileIO(PlasoFileIO):
  """Provide a file-like object to a file stored inside a TAR file."""

  def __init__(self, fh):
    """Constructor."""
    super(TarFileIO, self).__init__(fh)

  def read(self, size=None):
    """Read size bytes from file and return them."""
    if not self.fh:
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

    ret += self.fh.read(read_size)

    # In my testing I've seen the underlying read operation
    # sometimes read in way more than the size here indicates.
    # Slapping an additional check to make sure we return the amount
    # of bytes that we are really asking for.
    if size and len(ret) > size:
      self.buffer = ret[size:]
      ret = ret[:size]

    return ret

  def readline(self, size=-1):
    """Read a line from the file.

    Args:
      size: Defines the maximum byte count (including the new line trail)
      and if defined may get the function to return an incomplete line.

    Returns:
      A string containing a single line read from the file.
    """
    if not self.fh:
      return ''

    if '\n' not in self.buffer:
      self.buffer += self.fh.readline(size)

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

  def seek(self, offset, whence=0):
    """Seek into the filehandle."""
    if not self.fh:
      raise RuntimeError('Unable to seek into a file that is not open.')

    if whence == 1:
      if offset > 0 and len(self.buffer) > offset:
        self.buffer = self.buffer[offset:]
      else:
        ofs = offset - len(self.buffer)
        self.buffer = ''
        self.fh.seek(ofs, 1)
    else:
      self.buffer = ''
      self.fh.seek(offset, whence)

  def tell(self):
    """Return the current offset of the filehandle."""
    if not self.fh:
      return 0

    return self.fh.tell() - len(self.buffer)
