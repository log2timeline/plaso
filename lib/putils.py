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
import datetime
import tempfile

from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfile
from plaso.proto import transmission_pb2


class Options(object):
  """A simple configuration object."""


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


def FindAllParsers():
  """Find all available parser objects.

  A parser is defined as an object that implements the PlasoParser
  class and does not have the __abstract attribute set.

  Returns:
    A set of objects that implement the LogParser object.
  """
  pre_obj = Options()
  results = {}
  results['all'] = []
  parser_objs = _FindClasses(parser.PlasoParser, pre_obj)
  for parser_obj in parser_objs:
    results['all'].append(parser_obj)
    parser_type = parser_obj.PARSER_TYPE
    results.setdefault(parser_type, []).append(parser_obj)

  return results


def _FindClasses(class_object, *args):
  """Find all registered classes.

  A method to find all registered classes of a particular
  class.

  Args:
    class_object: The parent class.

  Returns:
    A list of registered classes of that class.
  """
  results = []
  for cl in class_object.classes:
    results.append(class_object.classes[cl](args))

  return results


def FindAllOutputs():
  """Find all available output modules."""
  return _FindClasses(output.LogOutputFormatter)


def PrintTimestamp(timestamp):
  """Print a human readable timestamp using ISO 8601 format."""
  epoch = int(timestamp / 1e6)
  my_date = (datetime.datetime.utcfromtimestamp(epoch) +
             datetime.timedelta(microseconds=(timestamp % 1e6)))

  return my_date.isoformat()


