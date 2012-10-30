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
"""This file contains log2timeline, the friendly front-end to plaso."""

import logging
import optparse
import sys

from plaso.lib import engine

# The number of bytes in a Mb.
BYTES_IN_A_MB = 1024 * 1024


if __name__ == '__main__':
  option_parser = optparse.OptionParser()

  option_parser.add_option('-z', '--zone', dest='tzone', action='store',
                           type='string', default='UTC',
                           help='Define the timezone of the IMAGE.')

  option_parser.add_option('-f', '--file', dest='filename', action='store',
                           default='.', metavar='FILE',
                           help='File we are about to parse.')

  option_parser.add_option('-r', '--recursive', dest='recursive',
                           action='store_true', default=False,
                           help='Turn on recursive mode.')

  option_parser.add_option('-p', '--preprocess', dest='preprocess',
                           action='store_true', default=False,
                           help='Turn on pre-processing.')

  option_parser.add_option('-w', '--write', dest='output', action='store',
                           default='/tmp/wheredidmytimelinego.dump',
                           metavar='FILE', help='The output file.')

  option_parser.add_option('--buffer-size', '--bs', dest='buffer_size',
                           action='store', default=0,
                           help='The buffer size for the output.')

  option_parser.add_option('--workers', dest='workers', action='store',
                           type='int', default=10,
                           help='The number of worker threads [default 10].')

  option_parser.add_option('-i', '--image', dest='image', action='store_true',
                           default=False, help='We are processing an image.')

  option_parser.add_option('--vss', dest='parse_vss', action='store_true',
                           default=False, help='Collect data from VSS.')

  option_parser.add_option('--single-thread', dest='single_thread',
                           action='store_true', default=False,
                           help=('Indicate that the tool should run in a '
                                 'single thread.'))

  option_parser.add_option('--open-files', dest='open_files',
                           action='store_true', default=False,
                           help=('Indicate that the tool should try to '
                                 'open files to extract embedded files within'
                                 ' them, for instance to extract files from '
                                 'compressed containers, etc.'))

  option_parser.add_option('--noopen-files', dest='open_files',
                           action='store_false',
                           help=('Indicate that the tool should NOT try to '
                                 'open files to extract embedded files within'
                                 ' them.'))

  option_parser.add_option('-o', '--offset', dest='image_offset',
                           action='store', default=0, type='int',
                           help='The sector offset to the image')

  option_parser.add_option('--ob', '--offset_bytes', dest='image_offset_bytes',
                           action='store', default=0, type='int',
                           help='The bytes offset to the image')

  option_parser.add_option('-d', '--debug', dest='debug', action='store_true',
                           default=False, help='Turn on debug information.')

  options, args = option_parser.parse_args()

  if options.tzone == 'list':
    print '=' * 40
    print '       ZONES'
    print '-' * 40
    for zone in engine.GetTimeZoneList():
      print '  %s' % zone
    print '=' * 40
    sys.exit(0)

  # This frontend only deals with local setup of the tool.
  options.local = True

  format_str = '[%(levelname)s] (%(processName)-10s) %(message)s'
  if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if options.buffer_size:
    if options.buffer_size[-1].lower() == 'm':
      options.buffer_size = int(options.buffer_size[:-1]) * BYTES_IN_A_MB
    else:
      try:
        options.buffer_size = int(options.buffer_size)
      except ValueError:
        logging.error(('Wrong usage: Buffer size needs to be an integer or'
                       ' end with M'))
        sys.exit(1)

  l2t = engine.Engine(options)
  try:
    l2t.Start()
  except KeyboardInterrupt:
    logging.warning('Tool being killed.')
    l2t.StopThreads()
