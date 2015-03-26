#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test run for a single file and a display of how many events are collected."""

import argparse
import cProfile
import logging
import os
import pstats
import sys
import time

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.proto import transmission_pb2
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.serializer import protobuf_serializer

from google.protobuf import text_format

try:
  # Support version 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # Support version older than 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

import pyevt
import pyevtx
import pylnk
import pymsiecf
import pyregf

import plaso
from plaso.engine import engine
from plaso.engine import single_process
from plaso.frontend import pprof
from plaso.frontend import psort
from plaso.frontend import utils as frontend_utils


def PrintHeader(options):
  """Print header information, including library versions."""
  print frontend_utils.FormatHeader('File Parsed')
  print u'{:>20s}'.format(options.file_to_parse)

  print frontend_utils.FormatHeader('Versions')
  print frontend_utils.FormatOutputString('plaso engine', plaso.GetVersion())
  print frontend_utils.FormatOutputString('pyevt', pyevt.get_version())
  print frontend_utils.FormatOutputString('pyevtx', pyevtx.get_version())
  print frontend_utils.FormatOutputString('pylnk', pylnk.get_version())
  print frontend_utils.FormatOutputString('pymsiecf', pymsiecf.get_version())
  print frontend_utils.FormatOutputString('pyregf', pyregf.get_version())

  if options.filter:
    print frontend_utils.FormatHeader('Filter Used')
    print frontend_utils.FormatOutputString('Filter String', options.filter)

  if options.parsers:
    print frontend_utils.FormatHeader('Parser Filter Used')
    print frontend_utils.FormatOutputString('Parser String', options.parsers)


def ProcessStorage(options):
  """Process a storage file and produce profile results.

  Args:
    options: the command line arguments (instance of argparse.Namespace).

  Returns:
    The profiling statistics or None on error.
  """
  storage_parameters = options.storage.split()
  storage_parameters.append(options.file_to_parse)

  if options.filter:
    storage_parameters.append(options.filter)

  if options.verbose:
    # TODO: why not move this functionality into psort?
    profiler = cProfile.Profile()
    profiler.enable()
  else:
    time_start = time.time()

  # Call psort and process output.
  return_value = psort.Main(storage_parameters)

  if options.verbose:
    profiler.disable()
  else:
    time_end = time.time()

  if return_value:
    print u'Parsed storage file.'
  else:
    print u'It appears the storage file may not have processed correctly.'

  if options.verbose:
    return GetStats(profiler)
  else:
    print frontend_utils.FormatHeader('Time Used')
    print u'{:>20f}s'.format(time_end - time_start)


def ProcessFile(options):
  """Process a file and produce profile results."""
  if options.proto_file and os.path.isfile(options.proto_file):
    with open(options.proto_file) as fh:
      proto_string = fh.read()

      proto = transmission_pb2.PathSpec()
      try:
        text_format.Merge(proto_string, proto)
      except text_format.ParseError as exception:
        logging.error(u'Unable to parse file, error: {}'.format(
            exception))
        sys.exit(1)

      serializer = protobuf_serializer.ProtobufPathSpecSerializer
      path_spec = serializer.ReadSerializedObject(proto)
  else:
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=options.file_to_parse)

  file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  if file_entry is None:
    logging.error(u'Unable to open file: {0:s}'.format(options.file_to_parse))
    sys.exit(1)

  # Set few options the engine expects to be there.
  # TODO: Can we rather set this directly in argparse?
  options.single_process = True
  options.debug = False
  options.text_prepend = u''

  # Set up the engine.
  # TODO: refactor and add queue limit.
  collection_queue = single_process.SingleProcessQueue()
  storage_queue = single_process.SingleProcessQueue()
  parse_error_queue = single_process.SingleProcessQueue()
  engine_object = engine.BaseEngine(
      collection_queue, storage_queue, parse_error_queue)

  # Create a worker.
  worker_object = engine_object.CreateExtractionWorker('0')
  # TODO: add support for parser_filter_string.
  worker_object.InitializeParserObjects()

  if options.verbose:
    profiler = cProfile.Profile()
    profiler.enable()
  else:
    time_start = time.time()
  worker_object.ParseFileEntry(file_entry)

  if options.verbose:
    profiler.disable()
  else:
    time_end = time.time()

  engine_object.SignalEndOfInputStorageQueue()

  event_object_consumer = pprof.PprofEventObjectQueueConsumer(storage_queue)
  event_object_consumer.ConsumeEventObjects()

  if not options.verbose:
    print frontend_utils.FormatHeader('Time Used')
    print u'{:>20f}s'.format(time_end - time_start)

  print frontend_utils.FormatHeader('Parsers Loaded')
  # Accessing protected member.
  # pylint: disable=protected-access
  plugins = []
  for parser_object in sorted(worker_object._parser_objects):
    print frontend_utils.FormatOutputString('', parser_object.NAME)
    parser_plugins = getattr(parser_object, '_plugins', [])
    plugins.extend(parser_plugins)

  print frontend_utils.FormatHeader('Plugins Loaded')
  for plugin in sorted(plugins):
    if isinstance(plugin, basestring):
      print frontend_utils.FormatOutputString('', plugin)
    else:
      plugin_string = getattr(plugin, 'NAME', u'N/A')
      print frontend_utils.FormatOutputString('', plugin_string)

  print frontend_utils.FormatHeader('Parsers Used')
  for parser in sorted(event_object_consumer.parsers):
    print frontend_utils.FormatOutputString('', parser)

  print frontend_utils.FormatHeader('Plugins Used')
  for plugin in sorted(event_object_consumer.plugins):
    print frontend_utils.FormatOutputString('', plugin)

  print frontend_utils.FormatHeader('Counter')
  for key, value in event_object_consumer.counter.most_common():
    print frontend_utils.FormatOutputString(key, value)

  if options.verbose:
    return GetStats(profiler)


def GetStats(profiler):
  """Print verbose information from profiler and return a stats object."""
  stats = pstats.Stats(profiler, stream=sys.stdout)
  print frontend_utils.FormatHeader('Profiler')

  print '\n{:-^20}'.format(' Top 10 Time Spent ')
  stats.sort_stats('cumulative')
  stats.print_stats(10)

  print '\n{:-^20}'.format(' Sorted By Function Calls ')
  stats.sort_stats('calls')
  stats.print_stats()

  return stats


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
      '--proto', dest='proto_file', action='store', default='', type=unicode,
      metavar='PROTO_FILE', help=(
          'A file containing an ASCII PathSpec protobuf describing how to '
          'open up the file for parsing.'))

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

  if not (options.file_to_parse or options.proto_file):
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error('Not able to run without a file to process.')
    return False

  if options.file_to_parse and not os.path.isfile(options.file_to_parse):
    logging.error(u'File [{0:s}] needs to exist.'.format(options.file_to_parse))
    return False

  PrintHeader(options)
  # Stats attribute used for console sessions.
  # pylint: disable=unused-variable
  if options.storage:
    stats = ProcessStorage(options)
  else:
    stats = ProcessFile(options)

  if options.console:
    ipshell = InteractiveShellEmbed()
    ipshell.confirm_exit = False
    ipshell()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
