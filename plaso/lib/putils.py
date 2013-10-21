#!/usr/bin/python
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
"""This file contains few methods for Plaso."""
import binascii
import fnmatch
import logging
import tempfile

from plaso.frontend import presets
from plaso.lib import event
from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfile
from plaso.lib import timelib
from plaso.lib import utils

import pytz


# TODO: Refactor the putils library so it does not end up being a trash can
# for all things core/front-end. We don't want this to be end up being a
# collection for all methods that have no other home.
class Options(object):
  """A simple configuration object."""


def _OpenImageFile(file_to_open, image_path, image_type='tsk',
                   image_offset=0, store_nr=0, fscache=None,
                   sector_size=512):
  """Return a PFile like object for a file in a raw disk image.

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
    A PFile object.
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

  return pfile.OpenPFile(pathspec, fscache=fscache)


def OpenTskFile(file_to_open, image_path, image_offset=0, fscache=None,
                sector_size=512):
  """Return a PFile like object for a file in a raw disk image.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    image_offset: Offset in sectors if this is a disk image.
    fscache: A FilesystemCache object that stores cached fs objects.
    sector_size: The size in bytes, defaults to 512.

  Returns:
    A PFile object.
  """
  return _OpenImageFile(
      file_to_open, image_path, 'tsk', image_offset, fscache=fscache,
      sector_size=sector_size)


def OpenOSFile(path):
  """Return a PFile like object for a file in the OS."""
  pathspec = event.EventPathSpec()
  pathspec.type = 'OS'
  pathspec.file_path = utils.GetUnicodeString(path)

  return pfile.OpenPFile(pathspec)


def OpenVssFile(file_to_open, image_path, store_nr, image_offset=0,
                fscache=None, sector_size=512):
  """Return a PFile like object for a file in an image inside a VSS.

  Args:
    file_to_open: A path or an inode number to the file in question.
    image_path: Full path to the image itself.
    store_nr: The store number (VSS store).
    image_offset: Offset in sectors if this is a disk image.
    fscache: A FilesystemCache object that stores cached fs objects.
    sector_size: The size in bytes, defaults to 512.

  Returns:
    A PFile object.
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


def FindAllParsers(pre_obj=None, parser_filter_string=''):
  """Find all available parser objects.

  A parser is defined as an object that implements the PlasoParser
  class and does not have the __abstract attribute set.

  The parser_filter_string is a simple comma separated value string that
  denotes a list of parser names to include. Each entry can have the value of:
    + Exact match of a list of parsers, or a preset (see
      plaso/frontend/presets.py for a full list of available presets).
    + A name of a single parser (case insensitive), eg. msiecfparser.
    + A glob name for a single parser, eg: '*msie*' (case insensitive).

  Each entry in the list can be prepended with a minus sign to signify a
  negative match against a parser, eg: 'winxp,-*lnk*' would select all the
  parsers in the "winxp" preset, EXCEPT parsers that have the substring "lnk"
  somewhere in the parser name.

  Args:
    pre_obj: A PlasoPreprocess object containing information collected from
        an image.
    parser_filter_string: A parser filter string, which is a comma
        separated value containing a list of parsers to include or exclude
        from the parser list.

  Returns:
    A dict that contains a list of all detected parsers. The key values in the
    dict will represent the type of the parser, eg 'all' will contain all
    parsers, while other keys will contain a subset of them, eg: 'sqlite' will
    contain parsers capable of parsing SQLite databases.
  """
  if not pre_obj:
    pre_obj = Options()

  # Process the filter string.
  filter_strings_include = []
  filter_strings_exclude = []
  for filter_string in parser_filter_string.split(','):
    filter_string = filter_string.strip()
    if not filter_string:
      continue
    if filter_string.startswith('-'):
      filter_strings_use = filter_strings_exclude
      filter_string = filter_string[1:]
    else:
      filter_strings_use = filter_strings_include

    filter_string_lower = filter_string.lower()
    if filter_string_lower in presets.categories:
      for preset_parser in presets.categories.get(filter_string_lower):
        filter_strings_use.append(preset_parser.lower())
    else:
      filter_strings_use.append(filter_string_lower)

  results = {}
  results['all'] = []
  for parser_obj in _FindClasses(parser.PlasoParser, pre_obj):
    add = False
    if not (filter_strings_exclude or filter_strings_include):
      add = True
    else:
      for include in filter_strings_include:
        if fnmatch.fnmatch(
            parser_obj.parser_name.lower(), '*%s*' % include):
          add = True

      for exclude in filter_strings_exclude:
        if fnmatch.fnmatch(
            parser_obj.parser_name.lower(), '*%s*' % exclude):
          add = False

    if add:
      results['all'].append(parser_obj)
      # TODO: Find a way to reintroduce PARSER_TYPE using other mechanism to
      # group parsers together.

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
    results.append(class_object.classes[cl](*args))

  return results


def FindAllOutputs():
  """Find all available output modules."""
  return _FindClasses(output.LogOutputFormatter, None)


def PrintTimestamp(timestamp):
  """Print a human readable timestamp using ISO 8601 format."""
  # TODO: this function is only used by frontend/pshell.py
  # refactor that code to use timelib and remove this function.
  return timelib.Timestamp.CopyToIsoFormat(timestamp, pytz.UTC)


def GetEventData(evt, fscache=None, before=0, length=20):
  """Return a hexdump like string of data surrounding event.

  This function takes an event object protobuf, opens the file
  that produced the event at the correct position, and creates
  a hex dump of the data, with both hexadecimal and ASCII
  characters printed out on the screen.

  Args:
    evt: The EventObject.
    fscache: A FilesystemCache object that stores cached fs objects.
    before: Number of bytes before the event that are included
    in the printout.
    length: Number of lines to print out in the hex output.

  Returns:
    A string containing a hexdump of the data surrounding the event.
  """
  if not evt:
    return u''

  if not hasattr(evt, 'pathspec'):
    return u''

  try:
    fh = pfile.OpenPFile(evt.pathspec.ToProto(), fscache=fscache)
  except IOError as e:
    return u'Error opening file: %s' % e

  offset = getattr(evt, 'offset', 0)
  if offset - before > 0:
    offset -= before

  return GetHexDumpStream(fh, offset, length)


def GetHexDumpStream(fh, offset, length=20):
  """Return a hex dump from a filehandle and an offset.

  Args:
    fh: A filehandle or a file like object.
    offset: The offset into the file like object where the first
    byte is read from.
    length: Number of lines to print. A single line consists of 16 bytes,
    making this variable a multiplier of 16 bytes.

  Returns:
    A string that contains the hex dump.
  """
  fh.seek(offset)
  data = fh.read(int(length) * 16)
  return GetHexDump(data, offset)


def GetHexDump(data, offset=0):
  """Return a hex dump from a data.

  Returns a hex dump of the data passed. Additionally all ASCII
  characters in the hex dump get translated back to their characters.

  Args:
    data: The binary data to be dumped into a hex string.
    offset: An optional start point in bytes where the data lies, for
    presentation purposes.

  Returns:
    A string that contains the hex dump.
  """
  hexdata = binascii.hexlify(data)
  data_out = []

  for entry_nr in range(0, len(hexdata) / 32):
    point = 32 * entry_nr
    data_out.append(GetHexDumpLine(hexdata[point:point + 32], offset, entry_nr))

  if len(hexdata) % 32:
    breakpoint = len(hexdata) / 32
    leftovers = hexdata[breakpoint:]
    pad = ' ' * (32 - len(leftovers))

    data_out.append(GetHexDumpLine(leftovers + pad, offset, breakpoint))

  return '\n'.join(data_out)


def GetHexDumpLine(line, orig_ofs, entry_nr=0):
  """Return a single line of 'xxd' dump like style."""
  out = []
  out.append('{0:07x}: '.format(orig_ofs + entry_nr * 16))

  for bit in range(0, 8):
    out.append('%s ' % line[bit * 4:bit * 4 + 4])

  for bit in range(0, 16):
    data = binascii.unhexlify(line[bit * 2: bit * 2 + 2])
    if ord(data) > 31 and ord(data) < 128:
      out.append(data)
    else:
      out.append('.')
  return ''.join(out)
