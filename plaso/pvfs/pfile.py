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
from plaso.proto import transmission_pb2
from plaso.pvfs import pfile_entry


PFILE_HANDLERS = {}


def InitPFile():
  """Creates a dict object with all PFile handlers."""
  for cls in pfile_entry.BaseFileEntry.classes:
    PFILE_HANDLERS[pfile_entry.BaseFileEntry.classes[cls].TYPE] = (
        pfile_entry.BaseFileEntry.classes[cls])


def OpenPFileEntry(spec, file_entry=None, orig=None, fscache=None):
  """Open up a BaseFileEntry object.

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
    spec: A PathSpec protobuf that describes the file that needs to be opened.
    file_entry: A file entry object that is used as base for extracting
                the needed file out.
    orig: A PathSpec protobuf that describes the root pathspec of the file.
    fscache: optional file system cache object. The default is None.

  Returns:
    A PFile object, that is a file like object.

  Raises:
    IOError: If the method is unable to open the file.
  """
  if not PFILE_HANDLERS:
    InitPFile()

  if isinstance(spec, basestring):
    spec_str = spec
    spec = event.EventPathSpec()
    spec.FromProtoString(spec_str)

  elif isinstance(spec, transmission_pb2.PathSpec):
    spec_proto = spec
    spec = event.EventPathSpec()
    spec.FromProto(spec_proto)

  handler_class = PFILE_HANDLERS.get(spec.type, 'UNSET')
  try:
    handler = handler_class(spec, root=orig, fscache=fscache)
  except errors.UnableToOpenFile:
    raise IOError(u'Unable to open the file: %s using %s' % (
        spec.file_path, spec.type))

  try:
    _ = handler.Open(file_entry)
  except IOError as e:
    raise IOError(u'[%s] Unable to open the file: %s, error: %s' % (
        handler.__class__.__name__, spec.file_path, e))

  if hasattr(spec, 'nested_pathspec'):
    if orig:
      orig_proto = orig
    else:
      orig_proto = spec
    return OpenPFileEntry(
        spec.nested_pathspec, file_entry=handler, orig=orig_proto,
        fscache=fscache)
  else:
    logging.debug(u'Opening file: %s [%s]', handler.name, spec.type)
    return handler

  raise IOError('Unable to open the file.')
