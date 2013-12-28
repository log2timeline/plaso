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
"""This file contains few methods for Plaso."""

import logging
import tempfile

from plaso.lib import event
from plaso.lib import utils
from plaso.pvfs import pfile


def _OpenImageFile(
    file_to_open, image_path, image_type='tsk', image_offset=0, store_nr=0,
    fscache=None, sector_size=512):
  """Opens a file entry object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_type: 'tsk' or 'vss' depending on the type of image being
    opened.
    image_offset: Offset in sectors if this is a disk image.
    store_nr: Applicaple only in the VSS sense, indicates the
    store number.
    fscache: A FilesystemCache object that stores cached fs objects.
    sector_size: The size in bytes, defaults to 512.

  Returns:
    A file entry object.
  """
  pathspec = event.EventPathSpec()
  if image_type == 'vss':
    pathspec.type = 'VSS'
    pathspec.vss_store_number = store_nr
  elif image_type == 'tsk':
    pathspec.type = 'TSK'

  else:
    logging.error('The currently supported types are: tsk or vss.')
    return

  pathspec.container_path = utils.GetUnicodeString(image_path)
  pathspec.image_offset = image_offset * sector_size
  if isinstance(file_to_open, (int, long)):
    pathspec.image_inode = file_to_open
  else:
    if '\\' in file_to_open:
      file_to_open = file_to_open.replace('\\', '/')
    pathspec.file_path = file_to_open

  return pfile.OpenPFileEntry(pathspec, fscache=fscache)


def OpenTskFileEntry(
    file_to_open, image_path, image_offset=0, fscache=None, sector_size=512):
  """Opens a file entry object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_offset: Offset in sectors if this is a disk image.
    fscache: A FilesystemCache object that stores cached fs objects.
    sector_size: The size in bytes, defaults to 512.

  Returns:
    A file entry object.
  """
  return _OpenImageFile(
      file_to_open, image_path, 'tsk', image_offset, fscache=fscache,
      sector_size=sector_size)


def OpenOSFileEntry(path):
  """Opens a file entry object based on an OS path."""
  pathspec = event.EventPathSpec()
  pathspec.type = 'OS'
  pathspec.file_path = utils.GetUnicodeString(path)

  return pfile.OpenPFileEntry(pathspec)


def OpenOSFileIO(path):
  """Opens a file-like object based on an OS path."""
  file_entry = OpenOSFileEntry(path)
  return file_entry.Open()


def OpenVssFileEntry(
    file_to_open, image_path, store_nr, image_offset=0, fscache=None,
    sector_size=512):
  """Opens a file entry object for a file in an image inside a VSS.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    store_nr: The store number (VSS store).
    image_offset: Offset in sectors if this is a disk image.
    fscache: A FilesystemCache object that stores cached fs objects.
    sector_size: The size in bytes, defaults to 512.

  Returns:
    A file entry object.
  """
  return _OpenImageFile(
      file_to_open, image_path, 'vss', image_offset, store_nr, fscache=fscache,
      sector_size=sector_size)


def Pfile2File(fh_in, path=None):
  """Save a PFile object into a "real" file.

  Args:
    fh_in: A PFile object.
    path: Full path to where the file should be saved.
          If not used then a temporary file will be allocated.

  Returns:
    The name of the file that was written out.
  """
  if path:
    fh_out = open(path, 'wb')
  else:
    fh_out = tempfile.NamedTemporaryFile()
    path = fh_out.name

  fh_in.seek(0)
  data = fh_in.read(32768)
  while data:
    fh_out.write(data)
    data = fh_in.read(32768)

  fh_out.close()
  return path
