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
import binascii
import os
import datetime
import logging
import tempfile

from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfile
from plaso.proto import transmission_pb2

# TODO: Refactor the putils library so it does not end up being a trash can
# for all things core/front-end. We don't want this to be end up being a
# collection for all methods that have no other home.


class Options(object):
  """A simple configuration object."""


def _OpenImageFile(file_to_open, image_path, image_type='tsk',
                   image_offset=0, store_nr=0):
  """Return a PFile like object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_type: 'tsk' or 'vss' depending on the type of image being
    opened.
    image_offset: Offset in sectors if this is a disk image.
    store_nr: Applicaple only in the VSS sense, indicates the
    store number.

  Returns:
    A PFile object.
  """
  if not os.path.isfile(image_path):
    logging.error(
        u'The image path is wrong, file does not exist: %s',
        image_path)
    return
  proto = transmission_pb2.PathSpec()
  if image_type == 'vss':
    proto.type = transmission_pb2.PathSpec.VSS
    proto.vss_store_number = store_nr
  elif image_type == 'tsk':
    proto.type = transmission_pb2.PathSpec.TSK

  else:
    logging.error('The currently supported types are: tsk or vss.')
    return

  proto.container_path = pfile.GetUnicodeString(image_path)
  proto.image_offset = image_offset * 512
  if isinstance(file_to_open, (int, long)):
    proto.image_inode = file_to_open
  else:
    if '\\' in file_to_open:
      file_to_open = file_to_open.replace('\\', '/')
    proto.file_path = file_to_open

  return pfile.OpenPFile(proto)


def OpenTskFile(file_to_open, image_path, image_offset=0):
  """Return a PFile like object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_offset: Offset in sectors if this is a disk image.

  Returns:
    A PFile object.
  """
  return _OpenImageFile(file_to_open, image_path, 'tsk', image_offset)


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
  return _OpenImageFile(
      file_to_open, image_path, 'vss', image_offset, store_nr)


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


def FindAllParsers(pre_obj=None, filters=None):
  """Find all available parser objects.

  A parser is defined as an object that implements the PlasoParser
  class and does not have the __abstract attribute set.

  Args:
    pre_obj: A PlasoPreprocess object containing information collected from
             image.
    filters: A Plaso Filter object.

  Returns:
    A set of objects that implement the LogParser object.
  """
  if not pre_obj:
    pre_obj = Options()

  # TODO: Add filter support.
  _ = filters

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


def GetEventData(event_proto, before=0):
  """Return a hexdump like string of data surrounding event.

  This function takes an event object protobuf, opens the file
  that produced the event at the correct position, and creates
  a XXD like style dump of the data, with hexadecimal and ASCII
  characters printed out on the screen.

  Args:
    event_proto: The EventObject protobuf.
    before: Number of bytes before the event that are included
    in the printout.

  Returns:
    A string containing a hexdump of the data surrounding the event.
  """
  if not event_proto:
    return u''

  try:
    fh = pfile.OpenPFile(event_proto.pathspec)
  except IOError as e:
    return u'Error opening file: %s' % e

  offset = 0
  if event_proto.HasField('offset'):
    offset = event_proto.offset

  if offset - before > 0:
    offset -= before

  fh.seek(offset)
  data = fh.read(10 * 32)
  hexdata = binascii.hexlify(data)
  data_out = []

  def FlushLine(line, orig_ofs, entry_nr=0):
    """Return a single line of 'xxd' dump like style."""
    out = []
    out.append('{0:07x}: '.format(orig_ofs + entry_nr * 16))

    for bit in range(0, 8):
      out.append('%s ' % line[bit * 4:bit * 4 + 4])

    for bit in range(0,16):
      data = binascii.unhexlify(line[bit * 2: bit * 2 + 2])
      if ord(data) > 31 and ord(data) < 128:
        out.append(data)
      else:
        out.append('.')
    return ''.join(out)

  for entry_nr in range(0, len(hexdata) / 32):
    point = 32 * entry_nr
    data_out.append(FlushLine(hexdata[point:point + 32], offset, entry_nr))

  if len(hexdata) % 32:
    breakpoint = len(hexdata) / 32
    leftovers = hexdata[breakpoint:]
    pad = ' ' * (32 - len(leftovers))

    data_out.append(FlushLine(leftovers + pad, offset, breakpoint))

  return '\n'.join(data_out)

