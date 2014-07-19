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

import argparse
import logging
import os
import random
import sys
import tempfile

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

try:
  # Support version 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # Support version older than 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

from IPython.config.loader import Config

# pylint: disable=unused-import
from plaso import analysis
from plaso import filters
from plaso import formatters
from plaso import output
from plaso import parsers
from plaso import preprocessors

from plaso.engine import collector
from plaso.engine import scanner
from plaso.engine import utils as engine_utils
from plaso.engine import worker

from plaso.frontend import frontend
from plaso.frontend import rpc_proxy
from plaso.frontend import utils as frontend_utils

from plaso.lib import binary
from plaso.lib import bufferlib
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import filter_interface
from plaso.lib import foreman
from plaso.lib import lexer
from plaso.lib import objectfilter
from plaso.lib import output as output_lib
from plaso.lib import parser
from plaso.lib import pfilter
from plaso.lib import plugin
from plaso.lib import process_info
from plaso.lib import proxy
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import registry as class_registry
from plaso.lib import storage
from plaso.lib import text_parser
from plaso.lib import timelib
from plaso.lib import utils

from plaso.output import helper as output_helper

from plaso.proto import plaso_storage_pb2

from plaso.serializer import interface as serializer_interface
from plaso.serializer import json_serializer
from plaso.serializer import protobuf_serializer

from plaso.unix import bsmtoken

from plaso.winnt import environ_expand
from plaso.winnt import knownfolderid

from plaso.winreg import cache as win_registry_cache
from plaso.winreg import interface as win_registry_interface
from plaso.winreg import path_expander
from plaso.winreg import utils as win_registry_utils
from plaso.winreg import winpyregf
from plaso.winreg import winregistry


class PshellFrontend(frontend.ExtractionFrontend):
  """Class that implements the pshell front-end."""

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(PshellFrontend, self).__init__(input_reader, output_writer)


def FindAllOutputs():
  """FindAllOutputs() - All available outputs."""
  return putils.FindAllOutputs()


def FindAllParsers():
  """Finds all available parsers."""
  return putils.FindAllParsers()


def GetEventData(event_proto, before=0):
  """Prints a hexdump of the event data."""
  return frontend_utils.OutputWriter.GetEventDataHexDump(event_proto, before)


def GetFileEntryFromEventObject(event_object):
  """Return a file entry object from a pathspec object.

  Args:
    event_object: An event object (an instance of EventObject).

  Returns:
    A file entry object (instance of vfs.file_entry.FileEntry) or
    None if the event object doesn't have a defined path spec.
  """
  path_spec = getattr(event_object, 'pathspec', None)

  if not path_spec:
    return

  return path_spec_resolver.Resolver.OpenFileEntry(path_spec)


def OpenOSFile(path):
  """Opens a file entry from the OS."""
  if not os.path.isfile(path):
    logging.error(u'File: {0:s} does not exist.'.format(path))
    return

  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_OS, location=path)
  return path_spec_resolver.Resolver.OpenFileEntry(path_spec)


def OpenStorageFile(storage_path):
  """Opens a storage file and returns the storage file object."""
  if not os.path.isfile(storage_path):
    return

  try:
    store = storage.StorageFile(storage_path, read_only=True)
  except IOError:
    print 'Unable to load storage file, not a storage file?'

  return store


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


def ParseFile(file_entry):
  """Parse a file given a file entry or path and return a list of results.

  Args:
    file_entry: Either a file entry object (instance of dfvfs.FileEntry)
                or a string containing a path (absolute or relative) to a
                local file.

  Returns:
    A list of event object (instance of EventObject) that were extracted from
    the file (or an empty list if no events were extracted).
  """
  if not file_entry:
    return

  if isinstance(file_entry, basestring):
    file_entry = OpenOSFile(file_entry)

  # Create the necessary items.
  proc_queue = queue.SingleThreadedQueue()
  storage_queue = queue.SingleThreadedQueue()
  storage_queue_producer = queue.EventObjectQueueProducer(storage_queue)
  pre_obj = event.PreprocessObject()
  all_parsers = putils.FindAllParsers(pre_obj)

  # Create a worker.
  worker_object = worker.EventExtractionWorker(
      'my_worker', proc_queue, storage_queue_producer, pre_obj, all_parsers)

  # Parse the file.
  worker_object.ParseFile(file_entry)

  storage_queue.SignalEndOfInput()
  proc_queue.SignalEndOfInput()

  results = []
  while True:
    try:
      item = storage_queue.PopItem()
    except errors.QueueEmpty:
      break

    if isinstance(item, queue.QueueEndOfInput):
      break

    results.append(item)
  return results


def Pfile2File(file_object, path):
  """Saves a file-like object to the path."""
  return frontend_utils.OutputWriter.WriteFile(file_object, path)


def PrintTimestamp(timestamp):
  """Prints a human readable timestamp from a timestamp value."""
  return frontend_utils.OutputWriter.GetDateTimeString(timestamp)


def PrintTimestampFromEvent(event_object):
  """Prints a human readable timestamp from values stored in an event object."""
  return PrintTimestamp(getattr(event_object, 'timestamp', 0))


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
  options.old_preprocess = False
  options.open_files = False
  options.output = os.path.join(temp_location, 'wheredidmytimelinego.dump')
  options.output_module = ''
  options.parsers = ''
  options.parse_vss = False
  options.preprocess = False
  options.recursive = False
  options.single_process = False
  options.timezone = 'UTC'
  options.workers = 5

  format_str = '[%(levelname)s] (%(processName)-10s) %(message)s'
  logging.basicConfig(format=format_str)

  front_end = PshellFrontend()

  try:
    front_end.ParseOptions(options, 'filename')
    front_end.SetStorageFile(options.output)
  except errors.BadConfigOption as exception:
    logging.error(u'{0:s}'.format(exception))

  # TODO: move to frontend object.
  if options.image and options.image_offset_bytes is None:
    if options.image_offset is not None:
      bytes_per_sector = getattr(options, 'bytes_per_sector', 512)
      options.image_offset_bytes = options.image_offset * bytes_per_sector
    else:
      options.image_offset_bytes = 0

  namespace = {}

  pre_obj = event.PreprocessObject()

  namespace.update(globals())
  namespace.update({
      'frontend': front_end, 'pre_obj': pre_obj, 'options': options,
      'find_all_output': FindAllOutputs, 'find_all_parsers': FindAllParsers,
      'parse_file': ParseFile, 'timestamp_from_event': PrintTimestampFromEvent,
      'message': formatters.manager.EventFormatterManager.GetMessageStrings})

  # Include few random phrases that get thrown in once the user exists the
  # shell.
  _my_random_phrases = [
      u'I haven\'t seen timelines like this since yesterday.',
      u'Timelining is super relaxing.',
      u'Why did I not use the shell before?',
      u'I like a do da cha cha',
      u'I AM the Shogun of Harlem!',
      (u'It doesn\'t matter if you win or lose, it\'s what you do with your '
       u'dancin\' shoes'),
      u'I have not had a night like that since the seventies.',
      u'Baker Team. They\'re all dead, sir.',
      (u'I could have killed \'em all, I could\'ve killed you. In town '
       u'you\'re the law, out here it\'s me.'),
      (u'Are you telling me that 200 of our men against your boy is a no-win '
       u'situation for us?'),
      u'Hunting? We ain\'t huntin\' him, he\'s huntin\' us!',
      u'You picked the wrong man to push',
      u'Live for nothing or die for something',
      u'I am the Fred Astaire of karate.',
      (u'God gave me a great body and it\'s my duty to take care of my '
       u'physical temple.'),
      u'This maniac should be wearing a number, not a badge',
      u'Imagination is more important than knowledge.',
      u'Do you hate being dead?',
      u'You\'ve got 5 seconds... and 3 are up.',
      u'He is in a gunfight right now. I\'m gonna have to take a message',
      u'That would be better than losing your teeth',
      u'The less you know, the more you make',
      (u'A SQL query goes into a bar, walks up to two tables and asks, '
       u'"Can I join you?"'),
      u'This is your captor speaking.',
      (u'If I find out you\'re lying, I\'ll come back and kill you in your '
       u'own kitchen.'),
      u'That would be better than losing your teeth',
      (u'He\'s the kind of guy who would drink a gallon of gasoline so '
       u'that he can p*ss into your campfire.'),
      u'I\'m gonna take you to the bank, Senator Trent. To the blood bank!',
      u'I missed! I never miss! They must have been smaller than I thought',
      u'Nah. I\'m just a cook.',
      u'Next thing I know, you\'ll be dating musicians.',
      u'Another cold day in hell',
      u'Yeah, but I bet you she doesn\'t see these boys in the choir.',
      u'You guys think you\'re above the law... well you ain\'t above mine!',
      (u'One thought he was invincible... the other thought he could fly... '
       u'They were both wrong'),
      u'To understand what recursion is, you must first understand recursion']

  arg_description = (
      u'pshell is the interactive session tool that can be used to'
      u'MISSING')

  arg_parser = argparse.ArgumentParser(description=arg_description)

  arg_parser.add_argument(
      '-s', '--storage_file', '--storage-file', dest='storage_file',
      type=unicode, default=u'', help=u'Path to a plaso storage file.',
      action='store', metavar='PATH')

  configuration = arg_parser.parse_args()

  if configuration.storage_file:
    store = OpenStorageFile(configuration.storage_file)
    if store:
      namespace.update({'store': store})

  functions = [
      FindAllOutputs, FindAllParsers, GetEventData, OpenOSFile, OpenStorageFile,
      OpenTskFile, OpenVssFile, ParseFile, Pfile2File, PrintTimestamp,
      PrintTimestampFromEvent]

  functions_strings = []
  for function in functions:
    docstring, _, _ = function.__doc__.partition(u'\n')
    docstring = u'\t{0:s} - {1:s}'.format(function.__name__, docstring)
    functions_strings.append(docstring)
  functions_strings = u'\n'.join(functions_strings)

  banner = (
      u'--------------------------------------------------------------\n'
      u' Welcome to Plaso console - home of the Plaso adventure land.\n'
      u'--------------------------------------------------------------\n'
      u'This is the place where everything is allowed, as long as it is '
      u'written in Python.\n\n'
      u'Objects available:\n\toptions - set of options to the frontend.\n'
      u'\tfrontend - A copy of the pshell frontend.\n'
      u'\n'
      u'All libraries have been imported and can be used, see help(frontend) '
      u'or help(parser).\n'
      u'\n'
      u'Base methods:\n'
      u'{0:s}'
      u'\n\tmessage - Print message strings from an event object.'
      u'\n'
      u'\n'
      u'p.s. typing in "pdb" and pressing enter puts the shell in debug'
      u'mode which causes all exceptions being sent to pdb.\n'
      u'Happy command line console fu-ing.\n\n').format(functions_strings)

  exit_message = u'You are now leaving the winter wonderland.\n\n{}'.format(
      random.choice(_my_random_phrases))

  shell_config = Config()
  # Make slight adjustments to the iPython prompt.
  shell_config.PromptManager.out_template = (
      r'{color.Normal}[{color.Red}\#{color.Normal}]<<< ')
  shell_config.PromptManager.in_template = (
      r'[{color.LightBlue}\T{color.Normal}] {color.LightPurple}\Y2\n'
      r'{color.Normal}[{color.Red}\#{color.Normal}] \$ ')
  shell_config.PromptManager.in2_template = r'.\D.>>>'

  ipshell = InteractiveShellEmbed(
      user_ns=namespace, config=shell_config, banner1=banner,
      exit_msg=exit_message)
  ipshell.confirm_exit = False
  # Set autocall to two, making parenthesis not necessary when calling
  # function names (although they can be used and are necessary sometimes,
  # like in variable assignements, etc).
  ipshell.autocall = 2
  ipshell()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
