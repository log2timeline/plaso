#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a console, the CLI friendly front-end to plaso."""

import logging
import os
import sys
import tempfile

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

try:
  # Support version 1.X of IPython.
  # pylint: disable-msg=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # Support version older than 1.X of IPython.
  # pylint: disable-msg=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

# pylint: disable-msg=unused-import
from plaso import filters
from plaso import formatters
from plaso import output
from plaso import parsers
from plaso import preprocessors

from plaso.frontend import preg
from plaso.frontend import psort
from plaso.frontend import utils as frontend_utils

from plaso.lib import engine
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import filter_interface
from plaso.lib import lexer
from plaso.lib import objectfilter
from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import registry as class_registry
from plaso.lib import storage
from plaso.lib import text_parser
from plaso.lib import timelib
from plaso.lib import worker

from plaso.output import helper

from plaso.proto import plaso_storage_pb2

from plaso.winreg import interface as win_registry_interface
from plaso.winreg import winregistry


def FindAllOutputs():
  """FindAllOutputs() - All available outputs."""
  return putils.FindAllOutputs()


def FindAllParsers():
  """Finds all available parsers."""
  return putils.FindAllParsers()


def GetEventData(event_proto, before):
  """Prints a hexdump of the event data."""
  return frontend_utils.OutputWriter.GetEventDataHexDump(event_proto, before)


def OpenVssFile(path, image_path, store_number, image_offset):
  """Opens a file entry inside a VSS inside an image file."""
  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_OS, location=image_path)

  if image_offset > 0:
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, start_offset=image_offset,
        parent=path_spec)
  else:
    volume_path_spec = path_spec

  store_number -= 1

  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_VSHADOW, store_index=store_number,
      parent=volume_path_spec)
  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_TSK, location=path, parent=path_spec)

  return path_spec_resolver.Resolver.OpenFileEntry(path_spec)


def OpenTskFile(image_path, image_offset, path=None, inode=None):
  """Opens a file entry of a file inside an image file."""
  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_OS, location=image_path)

  if image_offset > 0:
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, start_offset=image_offset,
        parent=path_spec)
  else:
    volume_path_spec = path_spec

  if inode is not None:
    if path is None:
      path = u''
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=inode, location=path,
        parent=volume_path_spec)
  else:
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, location=path, parent=volume_path_spec)

  return path_spec_resolver.Resolver.OpenFileEntry(path_spec)


def Pfile2File(file_object, path):
  """Saves a file-like object to the path."""
  return frontend_utils.OutputWriter.WriteFile(file_object, path)


def PrintTimestamp(timestamp):
  """Prints a human readable timestamp from values stored in an event object."""
  return frontend_utils.OutputWriter.GetDateTimeString(timestamp)


def Main():
  """Start the tool."""
  temp_location = tempfile.gettempdir()

  options = putils.Options()

  # Set the default options.
  options.buffer_size = 0
  options.debug = False
  options.filename = '.'
  options.file_filter = ''
  options.filter = ''
  options.image = False
  options.image_offset = None
  options.image_offset_bytes = None
  options.local = True
  options.old_preprocess = False
  options.open_files = False
  options.output = os.path.join(temp_location, 'wheredidmytimelinego.dump')
  options.output_module = ''
  options.parsers = ''
  options.parse_vss = False
  options.preprocess = False
  options.recursive = False
  options.single_thread = False
  options.tzone = 'UTC'
  options.workers = 5

  format_str = '[%(levelname)s] (%(processName)-10s) %(message)s'
  logging.basicConfig(format=format_str)

  l2t = engine.Engine(options)

  namespace = {}

  pre_obj = event.PreprocessObject()

  namespace.update(globals())
  namespace.update({'l2t': l2t, 'pre_obj': pre_obj, 'options': options})

  if len(sys.argv) > 1:
    test_file = sys.argv[1]
    if os.path.isfile(test_file):
      try:
        store = storage.StorageFile(test_file, read_only=True)
        namespace.update({'store': store})
      except IOError:
        print 'Unable to load storage file, not a storage file?'

  functions = [
      FindAllParsers, FindAllOutputs, PrintTimestamp, OpenVssFile, OpenTskFile,
      Pfile2File, GetEventData]

  functions_strings = []
  for function in functions:
    docstring, _, _ = function.__doc__.partition(u'\n')
    docstring = u'\t{0:s} - {1:s}'.format(function.__name__, docstring)
    functions_strings.append(docstring)
  functions_strings = u'\n'.join(functions_strings)

  banner = (
      '--------------------------------------------------------------\n'
      ' Welcome to Plaso console - home of the Plaso adventure land.\n'
      '--------------------------------------------------------------\n'
      'Objects available:\n\toptions - set of options to the engine.\n'
      '\tl2t - A copy of the log2timeline engine.\n'
      '\n'
      'All libraries have been imported and can be used, see help(pfile) '
      'or help(parser).\n'
      '\n'
      'Base methods:\n'
      '{0:s}'
      '\n'
      '\n'
      'Happy command line console fu-ing.').format(functions_strings)

  ipshell = InteractiveShellEmbed(
      user_ns=namespace, banner1=banner, exit_msg='')
  ipshell.confirm_exit = False
  ipshell()


if __name__ == '__main__':
  Main()
