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
"""This file contains a console, the CLI friendly front-end to plaso."""

# Pychecker supressions
__pychecker__ = 'unusednames=pyvshadow'

import datetime
import os
import logging
import tempfile

from IPython.frontend.terminal.embed import InteractiveShellEmbed

# pylint: disable=W0611
import pyvshadow

from plaso import output
from plaso import parsers
from plaso import preprocessors
from plaso import registry

from plaso.lib.putils import *

from plaso.lib import collector
from plaso.lib import engine
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import output
from plaso.lib import parser
from plaso.lib import pfile
from plaso.lib import preprocess
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


if __name__ == '__main__':
  temp_location = tempfile.gettempdir()

  options = Options()
  options.tzone = 'UTC'
  options.filename = '.'
  options.recursive = False
  options.preprocess = False
  options.output = os.path.join(temp_location, 'wheredidmytimelinego.dump')
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
            'Save a PFile object to a path in the OS.\n\tGetEventData(event'
            '_proto, before) - Print out a hexdump of the event for manual '
            'verification.\n\n'
            '\nHappy command line console fu-ing.')

  ipshell = InteractiveShellEmbed(user_ns=namespace, banner1=banner,
                                  exit_msg='')
  ipshell.confirm_exit = False
  ipshell()
