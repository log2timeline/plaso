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
"""This file contains classes to handle the transmission protobuf.

The classes are designed to create and process the transmission protobuf.
This involves opening up files and returning file entry and file-like objects
and creating protobufs that can accurately describe files and their locations
 so they can be successfully opened by Plaso.
"""

import logging

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import utils
from plaso.proto import transmission_pb2
from plaso.pvfs import pfile_entry
from plaso.pvfs import pfile_system
from plaso.pvfs import pvfs


PFILE_HANDLERS = {}


class PFileResolver(object):
  """Class that implements the pfile path specification resolver."""

  _fscache = pvfs.FilesystemCache()

  @classmethod
  def CopyPathToPathSpec(
      cls, path_spec_type, path, container_path=None, image_offset=None,
      inode_number=None, store_number=None):
    """Copies the path to a path specification equivalent."""
    path_spec = event.EventPathSpec()
    path_spec.type = path_spec_type
    path_spec.file_path = utils.GetUnicodeString(path)

    if path_spec_type in ['TSK', 'VSS']:
      if not container_path:
        raise RuntimeError(u'Missing container path.')

      path_spec.container_path = container_path
      if image_offset is not None:
        path_spec.image_offset = image_offset
      if inode_number is not None:
        path_spec.image_inode = inode_number

    if path_spec_type == 'VSS':
      if not store_number:
        raise RuntimeError(u'Missing store number.')
      path_spec.vss_store_number = store_number

    return path_spec

  @classmethod
  def OpenFileEntry(cls, path_spec, orig=None, file_entry=None):
    """Opens a file entry defined by path specification.

    The location and how to open the file is described in the PathSpec protobuf
    that includes location and information about which driver to use to open it.

    Each PathSpec can also define a nested PathSpec, if that file is stored
    within another file, or even an embedded one.

    An example PathSpec describing an image file that contains a GZIP compressed
    TAR file, that contains a GZIP compressed syslog file, providing multiple
    level of nested paths.

    type: TSK
    file_path: "/logs/sys.tgz"
    container_path: "test_data/syslog_image.dd"
    image_offset: 0
    image_inode: 12
    nested_pathspec {
      type: GZIP
      file_path: "/logs/sys.tgz"
      nested_pathspec {
        type: TAR
        file_path: "syslog.gz"
        container_path: "/logs/sys.tgz"
        nested_pathspec {
          type: GZIP
          file_path: "syslog.gz"
        }
      }
    }

    Args:
      path_spec: the VFS path specification (instance of path.PathSpec).
      orig: an optional path specification that describes the root of the file.
      file_entry: A file entry object that is used as base for extracting
                  the needed file out.

    Returns:
      The file entry (instance of PFileEntry) or None if the path
      specification could not be resolved.

    Raises:
      IOError: If the method is unable to open the file.
    """
    if not PFILE_HANDLERS:
      InitPFile()

    if isinstance(path_spec, basestring):
      path_spec_string = path_spec
      path_spec = event.EventPathSpec()
      path_spec.FromProtoString(path_spec_string)

    elif isinstance(path_spec, transmission_pb2.PathSpec):
      path_spec_proto = path_spec
      path_spec = event.EventPathSpec()
      path_spec.FromProto(path_spec_proto)

    handler_class = PFILE_HANDLERS.get(path_spec.type, 'UNSET')
    try:
      handler = handler_class(path_spec, root=orig, fscache=cls._fscache)
    except errors.UnableToOpenFile:
      raise IOError(u'Unable to open the file: {0:s} using {1:s}'.format(
          path_spec.file_path, path_spec.type))

    try:
      _ = handler.Open(file_entry)
    except IOError as e:
      raise IOError(
          u'[{0:s}] Unable to open the file: {1:s}, error: {2:s}'.format(
              handler.__class__.__name__, path_spec.file_path, e))

    if hasattr(path_spec, 'nested_pathspec'):
      if orig:
        orig_proto = orig
      else:
        orig_proto = path_spec
      return cls.OpenFileEntry(
          path_spec.nested_pathspec, orig=orig_proto, file_entry=handler)
    else:
      logging.debug(u'Opening file: {0:s} [{1:s}]'.format(
          handler.name, path_spec.type))
      return handler

    raise IOError(u'Unable to open the file.')

  @classmethod
  def OpenFileSystem(cls, path_spec):
    """Opens a file system defined by path specification."""
    if path_spec.type in ['TSK', 'VSS']:
      return cls._fscache.Open(
          path_spec.container_path, byte_offset=path_spec.image_offset)

    elif path_spec.type == 'OS':
      return pfile_system.OsFileSystem(path_spec.file_path)

    else:
      raise RuntimeError(u'Unsupported file system type.')


def InitPFile():
  """Creates a dict object with all PFile handlers."""
  for cls in pfile_entry.BaseFileEntry.classes:
    PFILE_HANDLERS[pfile_entry.BaseFileEntry.classes[cls].TYPE] = (
        pfile_entry.BaseFileEntry.classes[cls])
