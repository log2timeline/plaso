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
"""This file contains log2timeline, the friendly front-end to plaso."""
import argparse
import locale
import logging
import multiprocessing
import os
import sys
import time
import textwrap

from plaso.lib import errors
from plaso.lib import engine
from plaso.lib import info
from plaso.lib import pfilter
from plaso.lib import preprocess

# The number of bytes in a MiB.
BYTES_IN_A_MIB = 1024 * 1024


def Main():
  """Start the tool."""
  multiprocessing.freeze_support()
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
      log2timeline is the main frontend to the plaso backend, used to
      collect and correlate events extracted from a filesystem.

      More information can be gathered from here:
        http://plaso.kiddaland.net/usage/log2timeline
      """)
  arg_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description),
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog))

  # Create few argument groups to make formatting help messages clearer.
  info_group = arg_parser.add_argument_group('Informational Arguments')
  function_group = arg_parser.add_argument_group('Functional Arguments')
  deep_group = arg_parser.add_argument_group('Deep Analysis Arguments')
  performance_group = arg_parser.add_argument_group('Performance Arguments')

  function_group.add_argument(
      '-z', '--zone', dest='tzone', action='store', type=str, default='UTC',
      help=(
          'Define the timezone of the IMAGE (not the output). This is usually '
          'discovered automatically by pre processing but might need to be '
          'specifically set if pre processing does not properly detect or to '
          'overwrite the detected time zone.'))

  function_group.add_argument(
      '-t', '--text', dest='text_prepend', action='store', type=unicode,
      default=u'', metavar='TEXT', help=(
          'Define a free form text string that is prepended to each path '
          'to make it easier to distinguish one record from another in a '
          'timeline (like c:\, or host_w_c:\)'))

  function_group.add_argument(
      '--parsers', dest='parsers', type=str, action='store', default='',
      metavar='PARSER_LIST', help=(
          'Define a list of parsers to use by the tool. This is a comma '
          'separated list where each entry can be either a name of a parser '
          'or a parser list. Each entry can be prepended with a minus sign '
          'to negate the selection (not include it). The list match is an '
          'exact match while an individual parser matching can be a glob, '
          'as in "*reg*" would choose all parsers that have the word "reg" '
          'somewhere in it (matching is lowercase by default).'))

  function_group.add_argument(
      '-p', '--preprocess', dest='preprocess', action='store_true',
      default=False, help=(
          'Turn on pre-processing. Pre-processing is turned on by default '
          'when parsing image files, however if a mount point is being '
          'parsed then this parameter needs to be set manually.'))

  performance_group.add_argument(
      '--buffer-size', '--bs', dest='buffer_size', action='store', default=0,
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

  deep_group.add_argument(
      '--vss', dest='parse_vss', action='store_true', default=False,
      help=('Collect data from VSS. Off by default, this should be used on Wi'
            'ndows systems that have active VSS (Volume Shadow Copies) that n'
            'eed to be included in the analysis.'))

  deep_group.add_argument(
      '--vss-stores', dest='vss_stores', action='store', type=str, default=None,
      help=('List of stores to parse, format is X..Y where X and Y are intege'
            'rs, or a list of entries separated with a comma, eg: X,Y,Z or a '
            'list of ranges and entries, eg: X,Y-Z,G,H-J.'))

  performance_group.add_argument(
      '--single-thread', dest='single_thread', action='store_true',
      default=False,
      help='Indicate that the tool should run in a single thread.')

  function_group.add_argument(
      '-f', '--file_filter', dest='file_filter', action='store', type=str,
      default=None, help=('List of files to include for targeted collection of'
                          ' files to parse, one line per file path, setup is '
                          '/path|file - where each element can contain either'
                          ' a variable set in the preprocessing stage or a '
                          'regular expression'))

  deep_group.add_argument(
      '--scan-archives', dest='open_files', action='store_true', default=False,
      help=('Indicate that the tool should try to open files to extract embedd'
            'ed files within them, for instance to extract files from compress'
            'ed containers, etc. Be AWARE THAT THIS IS EXTREMELY SLOW.'))

  deep_group.add_argument(
      '--noscan-archives', dest='open_files', action='store_false',
      help=('Indicate that the tool should NOT try to '
            'open files to extract embedded files within them.'))

  function_group.add_argument(
      '-o', '--offset', dest='image_offset', action='store', default=0,
      type=int, help=(
          'The sector offset to the image in sector sizes (default to 512 '
          'bytes, possible to overwrite with --sector_size). '
          'If this option is used, then it is assumed we have an image '
          'file to parse, and using -i is not necessary.'))

  function_group.add_argument(
      '--ob', '--offset_bytes', dest='image_offset_bytes', action='store',
      default=0, type=int, help='The bytes offset to the image')

  info_group.add_argument(
      '-v', '--version', action='version',
      version='log2timeline - plaso backend %s' % engine.__version__,
      help='Show the current version of the backend.')

  info_group.add_argument(
      '--info', dest='show_info', action='store_true', default=False,
      help='Print out information about supported plugins and parsers.')

  function_group.add_argument(
      '--sector_size', dest='bytes_per_sector', action='store', type=int,
      default=512, help='The sector size, by default set to 512.')

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
      help=('The path to the output file, if the file exists it will get '
            'appended to.'))

  arg_parser.add_argument(
      'filename', action='store', metavar='FILENAME_OR_MOUNT_POINT',
      nargs='?', help=(
          'The path to the file, directory, image file or mount point that the'
          ' tool should parse. If this is a directory it will recursively go '
          'through it, same with an image file.'))

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTER', nargs='?', default=None,
      help=('A filter that can be used to filter the dataset before it '
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
        'give you time to cancel the runtime and reconfigure your preferred '
        'encoding, otherwise continue at own risk.')
    time.sleep(5)

  u_argv = [x.decode(preferred_encoding) for x in sys.argv]
  sys.argv = u_argv
  options = arg_parser.parse_args()
  options.preferred_encoding = preferred_encoding

  if options.tzone == 'list':
    print '=' * 40
    print '       ZONES'
    print '-' * 40
    for zone in engine.GetTimeZoneList():
      print '  %s' % zone
    print '=' * 40
    sys.exit(0)

  if options.show_info:
    print info.GetPluginInformation()
    sys.exit(0)

  # This frontend only deals with local setup of the tool.
  options.local = True

  format_str = '[%(levelname)s] (%(processName)-10s) %(message)s'
  if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if not options.output:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error(
        'Wrong usage: need to define an output.')
    sys.exit(1)

  if not options.filename:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error(u'No input file supplied.')
    sys.exit(1)

  options.recursive = os.path.isdir(options.filename)

  # Check to see if we are trying to parse a mount point.
  if options.recursive:
    file_collector = preprocess.FileSystemCollector(
        preprocess.PlasoPreprocess(), options.filename)
    guessed_os = preprocess.GuessOS(file_collector)
    if guessed_os != 'None':
      logging.info((
          u'Running against a mount point [{}]. Turning on '
          u'pre-processing.').format(
              guessed_os))
      options.preprocess = True
      logging.info(
          u'It is highly recommended to run the tool directly against '
          'the image, instead of parsing a mount point (you may get '
          'inconsistence results depending on the driver you use to mount '
          'the image. Please consider running against the raw image. A '
          '5 second wait has been introduced to give you time to read this '
          'over.')
      time.sleep(5)

  if options.filter and not pfilter.GetMatcher(options.filter):
    logging.error(
        (u'Filter error, unable to proceed. There is a problem with your '
         'filter: %s'), options.filter)
    sys.exit(1)

  if options.image_offset or options.image_offset_bytes:
    options.image = True

  if options.image:
    options.preprocess = True

  if options.buffer_size:
    if options.buffer_size[-1].lower() == 'm':
      options.buffer_size = int(options.buffer_size[:-1]) * BYTES_IN_A_MIB
    else:
      try:
        options.buffer_size = int(options.buffer_size)
      except ValueError:
        logging.error(('Wrong usage: Buffer size needs to be an integer or'
                       ' end with M'))
        sys.exit(1)

  if options.vss_stores:
    options.parse_vss = True
    stores = []
    try:
      for store in options.vss_stores.split(','):
        if '..' in store:
          begin, end = store.split('..')
          for nr in range(int(begin), int(end)):
            if nr not in stores:
              stores.append(nr)
        else:
          if int(store) not in stores:
            stores.append(int(store))
    except ValueError:
      arg_parser.print_help()
      print ''
      logging.error('VSS store range is wrongly formed.')
      sys.exit(1)

    options.vss_stores = sorted(stores)

  if options.parse_vss:
    options.image = True
    options.preprocess = True

  if options.file_filter:
    if not os.path.isfile(options.file_filter):
      logging.error(
          u'Error with collection filter, file: {} does not exist.'.format(
              options.file_filter))
      sys.exit(1)

  if options.workers < 1:
    # One worker for each "available" CPU (minus other processes).
    cpus = multiprocessing.cpu_count()
    options.workers = cpus
    if cpus > 3:
      options.workers -= 3

  try:
    l2t = engine.Engine(options)
  except errors.BadConfigOption as e:
    logging.warning(u'Unable to run tool, bad configuration: %s', e)
    sys.exit(1)

  try:
    l2t.Start()
    logging.info('Run completed.')
  except KeyboardInterrupt:
    logging.warning('Tool being killed.')
    l2t.StopThreads()


if __name__ == '__main__':
  Main()
