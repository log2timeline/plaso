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
"""This file contains a console, the CLI friendly front-end to plaso."""

import datetime
import logging
import tempfile

from IPython.frontend.terminal.embed import InteractiveShellEmbed

# pylint: disable=W0611
import pyvshadow

from plaso import output
from plaso import parsers
from plaso import preprocessors
from plaso import registry

from plaso.lib import collector
from plaso.lib import engine
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import registry as class_registry
from plaso.lib import sleuthkit
from plaso.lib import storage
from plaso.lib import timelib
from plaso.lib import vss
from plaso.lib import win_registry
from plaso.lib import win_registry_interface
from plaso.lib import worker

from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2
# pylint: enable=W0611


class Options(object):
  """A simple configuration object."""


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


def OpenOSFile(path):
  """Return a PFile like object for a file in the OS."""
  proto = transmission_pb2.PathSpec()
  proto.type = transmission_pb2.PathSpec.OS
  proto.file_path = pfile.GetUnicodeString(path)

  return pfile.OpenPFile(proto)


def FindAllParsers():
  """Find all available parser objects.

  A parser is defined as an object that implements the PlasoParser
  class and does not have the __abstract attribute set.

  Returns:
    A set of objects that implement the LogParser object.
  """
  pre_obj = preprocess.PlasoPreprocess()
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


if __name__ == '__main__':
  options = Options()
  options.tzone = 'UTC'
  options.filename = '.'
  options.recursive = False
  options.preprocess = False
  options.output = '/tmp/nowhere.dump'
  options.buffer_size = 0
  options.workers = 10
  options.image = False
  options.single_thread = False
  options.open_files = True
  options.image_offset = 0
  options.debug = False
  options.local = True
  format_str = '[%(levelname)s] (%(processName)-10s) %(message)s'
  logging.basicConfig(format=format_str)

  l2t = engine.Engine(options)

  namespace = {}

  namespace.update(globals())
  banner = ('--------------------------------------------------------------\n'
            ' Welcome to Plaso console - home of the Plaso adventure land.\n'
            '--------------------------------------------------------------\n'
            'Objects available:\n\toptions - set of options to the engine.'
            '\n\tl2t - A copy of the log2timeline engine.\n\n'
            'All libraries have been imported and can be used, see help(pfile)'
            ' or help(parser).\n\nBase methods:\n\tFindAllParsers() - All'
            ' available parser.\n\tFindAllOutputs() - All available outpu'
            'ts.\n\tOpenOSFile(path) - Open a PFile like object from a pa'
            'th.\n\tPrintTimestamp(timestamp) - Print a human readable ti'
            'mestamp from values stored in the EventObject.\n\tOpenVssFile'
            '(file_to_open, image_path, store_nr, image_offset) - Open a P'
            'File object from an image file, for a file inside a VSS.\n\t'
            'OpenTskFile(file_to_open, image_path, image_offset) - Open a P'
            'File object from an image file.\n\tPfile2File(fh_in, path) - '
            'Save a PFile object to a path in the OS.\n\n'
            '\nHappy command line console fu-ing.')

  ipshell = InteractiveShellEmbed(user_ns=namespace, banner1=banner,
                                  exit_msg='')
  ipshell.confirm_exit = False
  ipshell()
