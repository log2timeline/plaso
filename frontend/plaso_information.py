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
"""A simple dump information gathered from a plaso storage container."""
# To make YAML loading work.
__pychecker__ = 'no-import'
import argparse
import collections
import datetime
import logging
import os
import pprint
import sys

from plaso.lib import preprocess
from plaso.lib import storage
import pytz


def GetInformation(params):
  """Return generator for all potential storage information in a container."""
  store = storage.PlasoStorage(params.storage_file, read_only=True)
  infos = store.GetStorageInformation()

  if not infos:
    yield ''
    return

  for info in infos:
    yield DisplayInformation(info, params)


def DisplayInformation(info, params):
  """Return information gathered from storage."""
  header = u''
  information = u''
  printer = pprint.PrettyPrinter(indent=8)
  if hasattr(info, 'collection_information'):
    date = datetime.datetime.utcfromtimestamp(
        info.collection_information.get('time_of_run', 0))
    filename = info.collection_information.get('file_processed', 'N/A')

    header = (u'{0}\n\t\tPlaso Storage Information\n{0}\nStorage file: {3}\nFil'
              'e processed: {1}\nTime of processing: {2}\n').format(
                  '-' * 80, filename, date.isoformat(), params.storage_file)

    for key, value in info.collection_information.items():
      information += u'\t{0} = {1}\n'.format(key, value)

  if hasattr(info, 'counter'):
    information += u'\nCounter information:\n'
    for key, value in info.counter.most_common():
      information += u'\tCounter: %s = %d\n' % (key, value)

  if hasattr(info, 'stores'):
    information += u'\nStore information:\n'
    information += u'\tNumber of available stores: %d\n' % info.stores['Number']
    if params.verbose:
      for key, value in info.stores.items():
        if key == 'Number':
          continue
        information += u'\t%s =\n%s\n' % (key, printer.pformat(value))
    else:
      information += u'\tPrintout omitted (use verbose to see)\n'

  preprocessing = u'Pre-processing information:\n'
  if params.verbose:
    for key, value in info.__dict__.items():
      if key == 'collection_information':
        continue
      elif key == 'counter' or key == 'stores':
        continue
      if isinstance(value, list):
        preprocessing += u'\t{0} = \n{1}\n'.format(key, printer.pformat(value))
      else:
        preprocessing += u'\t{0} = {1}\n'.format(key, value)
  else:
    preprocessing = u'Preprocessing information omitted (run with verbose).'

  return u'{0}\n{1}\n{2}\n{3}'.format(
      header, information, preprocessing, '-+' * 40)


def Main():
  """Start the tool."""
  usage = """
Gives you information about the storage file, how it was
collected, what information was gained from the image, etc.
  """
  arg_parser = argparse.ArgumentParser(description=usage)

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  arg_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help='Be extra verbose in the information printed out.')

  arg_parser.add_argument(
      'storage_file', nargs='?', action='store', metavar='STORAGE FILE',
      default=None, help='The storage file.')

  options = arg_parser.parse_args()

  if not options.storage_file:
    arg_parser.print_help()
    print ''
    arg_parser.print_usage()
    print ''
    logging.error('Not able to run without a storage file being indicated.')
    sys.exit(1)

  if not os.path.isfile(options.storage_file):
    logging.error(
        u'File [%s] needs to exist, and be a proper plaso storage file.',
        options.storage_file)
    sys.exit(1)

  nothing = True
  for print_info in GetInformation(options):
    nothing = False
    print print_info

  if nothing:
    print u'No Plaso storage information found.'


if __name__ == '__main__':
  Main()
