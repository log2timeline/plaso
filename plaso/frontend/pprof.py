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
"""Test run for a single file and a display of how many events are collected."""

import argparse
import collections
import cProfile
import logging
import os
import pstats
import sys
import time

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

import pyevt
import pyevtx
import pylnk
import pymsiecf
import pyregf

import plaso
from plaso.frontend import psort
from plaso.lib import event
from plaso.lib import utils
from plaso.lib import queue
from plaso.lib import worker


# TODO: Remove this after the dfVFS integration.
# TODO: Make sure we don't need to imlement the method _ConsumeItem, or
# to have that not as an abstract method.
# pylint: disable-msg=abstract-method
class PprofEventObjectQueueConsumer(queue.EventObjectQueueConsumer):
  """Class that implements an event object queue consumer for pprof."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(PprofEventObjectQueueConsumer, self).__init__(queue_object)
    self.counter = collections.Counter()
    self.parsers = []

  def _ConsumeEventObject(self, event_object):
    """Consumes an event object callback for ConsumeEventObject."""
    parser = getattr(event_object, 'parser', 'N/A')
    if parser not in self.parsers:
      self.parsers.append(parser)

    self.counter[parser] += 1
    self.counter['Total'] += 1


def Main():
  """Start the tool."""
  usage = (
      u'Run this tool against a single file to see how many events are '
      u'extracted from it and which parsers recognize it.')

  arg_parser = argparse.ArgumentParser(description=usage)

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  arg_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help=(
          'Be extra verbose in the information printed out (include full '
          'stats).'))

  arg_parser.add_argument(
      '-c', '--console', dest='console', action='store_true',
      default=False, help='After processing drop to an interactive shell.')

  arg_parser.add_argument(
      '-p', '--parsers', dest='parsers', action='store', default='', type=str,
      help='A list of parsers to include (see log2timeline documentation).')

  arg_parser.add_argument(
      '-s', '--storage', dest='storage', action='store', type=unicode,
      metavar='PSORT_PARAMETER', default='', help=(
          'Run the profiler against a storage file, with the parameters '
          'provided with this option, eg: "-q -w /dev/null". The storage '
          'file has to be passed in as the FILE_TO_PARSE argument to the '
          'tool and filters are also optional. This is equivilant to calling '
          'psort.py STORAGE_PARAMETER FILE_TO_PARSE [FILTER]. Where the '
          'storage parameters are the ones defined with this parameter.'))

  # TODO: Add the option of dropping into a python shell that contains the
  # stats attribute and others, just print out basic information and do the
  # profiling, then drop into a ipython shell that allows you to work with
  # the stats object.

  arg_parser.add_argument(
      'file_to_parse', nargs='?', action='store', metavar='FILE_TO_PARSE',
      default=None, help='A path to the file that is to be parsed.')

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTER', nargs='?', default=None,
      help=('A filter that can be used to filter the dataset before it '
            'is written into storage. More information about the filters'
            ' and it\'s usage can be found here: http://plaso.kiddaland.'
            'net/usage/filters'))

  options = arg_parser.parse_args()

  if not options.file_to_parse:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error('Not able to run without a file to process.')
    sys.exit(1)

  if not os.path.isfile(options.file_to_parse):
    logging.error(u'File [{0:s}] needs to exist.'.format(options.file_to_parse))
    sys.exit(1)

  PrintHeader(options)
  # Stats attribute used for console sesssions.
  # pylint: disable-msg=unused-variable
  if options.storage:
    stats = ProcessStorage(options)
  else:
    stats = ProcessFile(options)

  if options.console:
    ipshell = InteractiveShellEmbed()
    ipshell.confirm_exit = False
    ipshell()


def PrintHeader(options):
  """Print header information, including library versions."""
  print utils.FormatHeader('File Parsed')
  print u'{:>20s}'.format(options.file_to_parse)

  print utils.FormatHeader('Versions')
  print utils.FormatOutputString('plaso engine', plaso.GetVersion())
  print utils.FormatOutputString('pyevt', pyevt.get_version())
  print utils.FormatOutputString('pyevtx', pyevtx.get_version())
  print utils.FormatOutputString('pylnk', pylnk.get_version())
  print utils.FormatOutputString('pymsiecf', pymsiecf.get_version())
  print utils.FormatOutputString('pyregf', pyregf.get_version())

  if options.filter:
    print utils.FormatHeader('Filter Used')
    print utils.FormatOutputString('Filter String', options.filter)

  if options.parsers:
    print utils.FormatHeader('Parser Filter Used')
    print utils.FormatOutputString('Parser String', options.parsers)


def ProcessStorage(options):
  """Process a storage file and produce profile results."""
  storage_parameters = options.storage.split()
  storage_parameters.append(options.file_to_parse)
  if options.filter:
    storage_parameters.append(options.filter)

  arguments = psort.ProcessArguments(storage_parameters)

  if options.verbose:
    profiler = cProfile.Profile()
    profiler.enable()
  else:
    time_start = time.time()

  # Call psort and process output.
  psort.Main(arguments)

  if options.verbose:
    profiler.disable()
  else:
    time_end = time.time()

  if options.verbose:
    return GetStats(profiler)
  else:
    print utils.FormatHeader('Time Used')
    print u'{:>20f}s'.format(time_end - time_start)


def ProcessFile(options):
  """Process a file and produce profile results."""
  path_spec = path_spec_factory.Factory.NewPathSpec(
      definitions.TYPE_INDICATOR_OS, location=options.file_to_parse)
  file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  if file_entry is None:
    logging.error(u'Unable to open file: {0:s}'.format(options.file_to_parse))
    sys.exit(1)

  pre_obj = event.PreprocessObject()
  storage_queue = queue.SingleThreadedQueue()
  storage_queue_producer = queue.EventObjectQueueProducer(storage_queue)
  my_worker = worker.EventExtractionWorker(
      '0', None, storage_queue_producer, config=options, pre_obj=pre_obj)

  if options.verbose:
    profiler = cProfile.Profile()
    profiler.enable()
  else:
    time_start = time.time()
  my_worker.ParseFile(file_entry)

  if options.verbose:
    profiler.disable()
  else:
    time_end = time.time()

  storage_queue_producer.SignalEndOfInput()

  event_object_consumer = PprofEventObjectQueueConsumer(storage_queue)
  event_object_consumer.ConsumeEventObjects()

  if not options.verbose:
    print utils.FormatHeader('Time Used')
    print u'{:>20f}s'.format(time_end - time_start)

  print utils.FormatHeader('Parsers Loaded')
  # Accessing protected member.
  # pylint: disable-msg=protected-access
  for parser in sorted(my_worker._parsers['all']):
    print utils.FormatOutputString('', parser.parser_name)

  print utils.FormatHeader('Parsers Used')
  for parser in sorted(event_object_consumer.parsers):
    print utils.FormatOutputString('', parser)

  print utils.FormatHeader('Counter')
  for key, value in event_object_consumer.counter.most_common():
    print utils.FormatOutputString(key, value)

  if options.verbose:
    return GetStats(profiler)


def GetStats(profiler):
  """Print verbose information from profiler and return a stats object."""
  stats = pstats.Stats(profiler, stream=sys.stdout)
  print utils.FormatHeader('Profiler')

  print '\n{:-^20}'.format(' Top 10 Time Spent ')
  stats.sort_stats('cumulative')
  stats.print_stats(10)

  print '\n{:-^20}'.format(' Sorted By Function Calls ')
  stats.sort_stats('calls')
  stats.print_stats()

  return stats


if __name__ == '__main__':
  Main()
