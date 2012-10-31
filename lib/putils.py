#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
from plaso.lib import pfile
from plaso.proto import transmission_pb2


def OpenTskFile(file_to_open, image_path, image_offset=0):
  """Return a PFile like object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_offset: Offset in sectors if this is a disk image.

  Returns:
    A PFile object.
  """
  proto = transmission_pb2.PathSpec()
  proto.type = transmission_pb2.PathSpec.TSK
  proto.container_path = pfile.GetUnicodeString(image_path)
  proto.image_offset = image_offset * 512
  if isinstance(file_to_open, (int, long)):
    proto.image_inode = file_to_open
  else:
    proto.file_path = file_to_open

  return pfile.OpenPFile(proto)


def OpenOSFile(path):
  """Return a PFile like object for a file in the OS."""
  proto = transmission_pb2.PathSpec()
  proto.type = transmission_pb2.PathSpec.OS
  proto.file_path = pfile.GetUnicodeString(path)

  return pfile.OpenPFile(proto)


def OpenVssFile(file_to_open, image_path, store_nr, image_offset=0):
  """Return a PFile like object for a file in an image inside a VSS.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    store_nr: The store number (VSS store).
    image_offset: Offset in sectors if this is a disk image.

  Returns:
    A PFile object.
  """
  proto = transmission_pb2.PathSpec()
  proto.type = transmission_pb2.PathSpec.VSS
  proto.vss_store_number = store_nr
  proto.container_path = pfile.GetUnicodeString(image_path)
  proto.image_offset = image_offset * 512
  if isinstance(file_to_open, (int, long)):
    proto.image_inode = file_to_open
  else:
    proto.file_path = file_to_open

  return pfile.OpenPFile(proto)
