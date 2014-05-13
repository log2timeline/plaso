#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""The log2timeline front-end."""

import argparse
import locale
import logging
import multiprocessing
import sys
import time
import textwrap

import pytsk3

import plaso
from plaso.frontend import frontend
from plaso.lib import engine
from plaso.lib import errors
from plaso.lib import info
from plaso.lib import pfilter
from plaso.preprocessors import interface as preprocess_interface

import pytz


class LoggingFilter(logging.Filter):
  """Class that implements basic filtering of log events for plaso.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters down the debug logs of plaso, making them
  almost non-usable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure."""
    if record.module == 'binplist' and record.levelno == logging.DEBUG:
      return False

    return True


class Log2TimelineFrontend(frontend.ExtractionFrontend):
  """Class that implements the log2timeline front-end."""

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = engine.StdinEngineInputReader()
    output_writer = engine.StdoutEngineOutputWriter()

    super(Log2TimelineFrontend, self).__init__(input_reader, output_writer)

  # TODO: move or rewrite this after dfVFS image support integration.
  def GetPartitionMap(self, image_path):
    """Returns a list of dict objects representing partition information.

    Args:
      image_path: The path to the image file.

    Returns:
      A list that contains a dict object for each partition in the image. The
      dict contains the partition number (address), description of it alongside
      an offset and length of the partition size.

    Raises:
      UnableToOpenFilesystem: if the parition map cannot be determined.
    """
    partition_map = []
    try:
      img = pytsk3.Img_Info(image_path)
    except IOError as exception:
      raise errors.UnableToOpenFilesystem(
          u'Unable to open image file with error: {0:s}'.format(exception))

    try:
      volume = pytsk3.Volume_Info(img)
    except IOError as exception:
      raise errors.UnableToOpenFilesystem(
          u'Unable to open file system with error: {0:s}'.format(exception))

    block_size = getattr(volume.info, 'block_size', 512)
    partition_map.append(block_size)

    for part in volume:
      partition_map.append({
          'address': part.addr,
          'description': part.desc,
          'offset': part.start,
          'length': part.len})

    return partition_map

  def GetTimeZoneList(self):
    """Returns a generator of the names of all the supported time zones."""
    yield 'local'
    for zone in pytz.all_timezones:
      yield zone

  def PrintParitionMap(self, source):
    """Prints the partition map.

    Args:
      source: the source to retrieve the partion map from.
    """
    partition_map = self.GetPartitionMap(source)

    print 'Sector size: {}'.format(partition_map[0])
    print u'Index  {:10s} {:10s} {}'.format('Offset', 'Length', 'Description')
    for entry in partition_map[1:]:
      print u'{:02d}:    {:010d} {:010d} {}'.format(
          entry['address'], entry['offset'], entry['length'],
          entry['description'])


def Main():
  """Start the tool."""
  multiprocessing.freeze_support()

  front_end = Log2TimelineFrontend()

  epilog = (
      """
      Example usage:

      Run the tool against an image (full kitchen sink)
          log2timeline.py -o 63 /cases/mycase/plaso.dump image.dd

      Same as before except this time include VSS information as well.
          log2timeline.py -o 63 --vss /cases/mycase/plaso_vss.dump image.dd

      And that's how you build a timeline using log2timeline...
      """)
  description = (
      """
      log2timeline is the main front-end to the plaso back-end, used to
      collect and correlate events extracted from a filesystem.

      More information can be gathered from here:
        http://plaso.kiddaland.net/usage/log2timeline
      """)
  arg_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description),
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog), add_help=False)

  # Create few argument groups to make formatting help messages clearer.
  info_group = arg_parser.add_argument_group('Informational Arguments')
  function_group = arg_parser.add_argument_group('Functional Arguments')
  deep_group = arg_parser.add_argument_group('Deep Analysis Arguments')
  performance_group = arg_parser.add_argument_group('Performance Arguments')

  function_group.add_argument(
      '-z', '--zone', dest='tzone', action='store', type=str, default='UTC',
      help=(
          'Define the timezone of the IMAGE (not the output). This is usually '
          'discovered automatically by preprocessing but might need to be '
          'specifically set if preprocessing does not properly detect or to '
          'overwrite the detected time zone.'))

  function_group.add_argument(
      '-t', '--text', dest='text_prepend', action='store', type=unicode,
      default=u'', metavar='TEXT', help=(
          r'Define a free form text string that is prepended to each path '
          r'to make it easier to distinguish one record from another in a '
          r'timeline (like c:\, or host_w_c:\)'))

  function_group.add_argument(
      '--parsers', dest='parsers', type=str, action='store', default='',
      metavar='PARSER_LIST', help=(
          'Define a list of parsers to use by the tool. This is a comma '
          'separated list where each entry can be either a name of a parser '
          'or a parser list. Each entry can be prepended with a minus sign '
          'to negate the selection (exclude it). The list match is an '
          'exact match while an individual parser matching is a case '
          'insensitive substring match, with support for glob patterns. '
          'Examples would be: "reg" that matches the substring "reg" in '
          'all parser names or the glob pattern "sky[pd]" that would match '
          'all parsers that have the string "skyp" or "skyd" in it\'s name. '
          'All matching is case insensitive.'))

  info_group.add_argument(
      '-h', '--help', action='help', help='Show this help message and exit.')

  info_group.add_argument(
      '--logfile', action='store', metavar='FILENAME', dest='logfile',
      type=unicode, default=u'', help=(
          'If defined all log messages will be redirected to this file instead '
          'the default STDERR.'))

  function_group.add_argument(
      '-p', '--preprocess', dest='preprocess', action='store_true',
      default=False, help=(
          'Turn on preprocessing. Preprocessing is turned on by default '
          'when parsing image files, however if a mount point is being '
          'parsed then this parameter needs to be set manually.'))

  performance_group.add_argument(
      '--buffer_size', '--buffer-size', '--bs', dest='buffer_size',
      action='store', default=0,
      help='The buffer size for the output (defaults to 196MiB).')

  performance_group.add_argument(
      '--workers', dest='workers', action='store', type=int, default=0,
      help=('The number of worker threads [defaults to available system '
            'CPU\'s minus three].'))

  function_group.add_argument(
      '-i', '--image', dest='image', action='store_true', default=False,
      help=(
          'Indicates that this is an image instead of a regular file. It is '
          'not necessary to include this option if -o (offset) is used, then '
          'this option is assumed. Use this when parsing an image with an '
          'offset of zero.'))

  front_end.AddVssProcessingOptions(deep_group)

  performance_group.add_argument(
      '--single_thread', '--single-thread', dest='single_thread',
      action='store_true', default=False,
      help='Indicate that the tool should run in a single thread.')

  function_group.add_argument(
      '-f', '--file_filter', '--file-filter', dest='file_filter',
      action='store', type=unicode, default=None, help=(
          'List of files to include for targeted collection of files to parse, '
          'one line per file path, setup is /path|file - where each element '
          'can contain either a variable set in the preprocessing stage or a '
          'regular expression'))

  deep_group.add_argument(
      '--scan_archives', dest='open_files', action='store_true', default=False,
      help=argparse.SUPPRESS)

  # This option is "hidden" for the time being, still left in there for testing
  # purposes, but hidden from the tool usage and help messages.
  #    help=('Indicate that the tool should try to open files to extract embedd'
  #          'ed files within them, for instance to extract files from compress'
  #          'ed containers, etc. Be AWARE THAT THIS IS EXTREMELY SLOW.'))

  front_end.AddImageOptions(function_group)

  function_group.add_argument(
      '--partition', dest='partition_number', action='store', type=int,
      default=None, help=(
          'Choose a partition number from a disk image. This partition '
          'number should correspond to the number displayed from the parameter'
          ' --partition_map.'))

  # Build the version information.
  version_string = u'log2timeline - plaso back-end {}'.format(
      plaso.GetVersion())

  info_group.add_argument(
      '-v', '--version', action='version', version=version_string,
      help='Show the current version of the back-end.')

  info_group.add_argument(
      '--info', dest='show_info', action='store_true', default=False,
      help='Print out information about supported plugins and parsers.')

  info_group.add_argument(
      '--partition_map', '--partition-map', action='store_true',
      dest='partition_map', default=False, help=(
          'Print out a partition map of a disk image.'))

  function_group.add_argument(
      '--use_old_preprocess', '--use-old-preprocess', dest='old_preprocess',
      action='store_true', default=False, help=(
          'Only used in conjunction when appending to a previous storage '
          'file. When this option is used then a new preprocessing object '
          'is not calculated and instead the last one that got added to '
          'the storage file is used. This can be handy when parsing an image '
          'that contains more than a single partition.'))

  function_group.add_argument(
      '--output', dest='output_module', action='store', type=unicode,
      default='', help=(
          'Bypass the storage module directly storing events according to '
          'the output module. This means that the output will not be in the '
          'pstorage format but in the format chosen by the output module. '
          '[Please not this feature is EXPERIMENTAL at this time, use at '
          'own risk (eg. sqlite output does not yet work)]'))

  info_group.add_argument(
      '-d', '--debug', dest='debug', action='store_true', default=False,
      help='Turn on debug information in the tool.')

  arg_parser.add_argument(
      'output', action='store', metavar='STORAGE_FILE', nargs='?',
      type=unicode, help=(
          'The path to the output file, if the file exists it will get '
          'appended to.'))

  arg_parser.add_argument(
      'source', action='store', metavar='SOURCE',
      nargs='?', type=unicode, help=(
          'The path to the source device, file or directory. If the source is '
          'a supported storage media device or image file, archive file or '
          'a directory, the files within are processed recursively.'))

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTER', nargs='?', default=None,
      type=unicode, help=(
          'A filter that can be used to filter the dataset before it '
          'is written into storage. More information about the filters'
          ' and it\'s usage can be found here: http://plaso.kiddaland.'
          'net/usage/filters'))

  # Properly prepare the attributes according to local encoding.
  preferred_encoding = locale.getpreferredencoding()
  if preferred_encoding.lower() == 'ascii':
    logging.warning(
        u'The preferred encoding of your system is ASCII, which is not optimal '
        u'for the typically non-ASCII characters that need to be parsed and '
        u'processed. The tool will most likely crash and die, perhaps in a way '
        u'that may not be recoverable. A five second delay is introduced to '
        u'give you time to cancel the runtime and reconfigure your preferred '
        u'encoding, otherwise continue at own risk.')
    time.sleep(5)

  u_argv = [x.decode(preferred_encoding) for x in sys.argv]
  sys.argv = u_argv
  options = arg_parser.parse_args()
  options.preferred_encoding = preferred_encoding

  if options.tzone == 'list':
    print '=' * 40
    print '       ZONES'
    print '-' * 40
    for zone in front_end.GetTimeZoneList():
      print '  {0:s}'.format(zone)
    print '=' * 40
    return True

  if options.show_info:
    print info.GetPluginInformation()
    return True

  format_str = (
      u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
      u'<%(module)s> %(message)s')

  if options.debug:
    if options.logfile:
      logging.basicConfig(
          level=logging.DEBUG, format=format_str, filename=options.logfile)
    else:
      logging.basicConfig(level=logging.DEBUG, format=format_str)

    logging_filter = LoggingFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(logging_filter)
  elif options.logfile:
    logging.basicConfig(
        level=logging.INFO, format=format_str, filename=options.logfile)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if not options.output:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error(u'Wrong usage: need to define an output.')
    return False

  if options.partition_map:
    if options.source:
      source = options.source
    else:
      source = options.output

    try:
      front_end.PrintParitionMap(source)
    except errors.UnableToOpenFilesystem as exception:
      print exception
      return False
    return True

  if not options.source:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error(u'No input source supplied.')
    return False

  if options.filter and not pfilter.GetMatcher(options.filter):
    logging.error((
        u'Filter error, unable to proceed. There is a problem with your '
        u'filter: {0:s}').format(options.filter))
    return False

  try:
    front_end.ParseOptions(options, 'source')
    front_end.SetStorageFile(options.output)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print ''
    logging.error('{0:s}'.format(exception))
    return False

  # Check to see if we are trying to parse a mount point.
  if getattr(options, 'recursive', False):
    searcher = front_end.GetSourceFileSystemSearcher()

    guessed_os = preprocess_interface.GuessOS(searcher)
    if guessed_os != 'None':
      options.preprocess = True
      logging.info((
          u'Running against a mount point [{0:s}]. Turning on '
          u'preprocessing.').format(guessed_os))
      logging.warning(
          u'It is highly recommended to run the tool directly against '
          u'the image, instead of parsing a mount point (you may get '
          u'inconsistence results depending on the driver you use to mount '
          u'the image. Please consider running against the raw image. '
          u'Processing will continue in 5 seconds.')
      time.sleep(5)

  try:
    front_end.ProcessSource(options)
    logging.info(u'Processing completed.')
  except KeyboardInterrupt:
    logging.warning(u'Aborted by user.')
    front_end.CleanUpAfterAbort()
    return False
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
