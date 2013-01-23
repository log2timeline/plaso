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
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  ./psort
  --storagefile=$PATH_TO_PLASO_CONTAINER
  --first_time="2012-10-10 14:18:56" --last_time="2012-10-10 14:24:20"
  or
  --first_time_microsec=1349893136000000 --last_time_microsec=1349893460000000
  --output_format=L2tCsv
  --zone="US/Eastern"
  --write=output_filename.txt

For further details about the storage design see:
https://sites.google.com/a/kiddaland.net/plaso/developer/libraries/storage

This utility should resemble the section entitiled 'External Merge'
"""

import calendar
import heapq
import logging
import pdb
import sys

import argparse
import dateutil.parser
import pytz

from plaso import output
from plaso import parsers
from plaso.lib import event
from plaso.lib import output as output_lib
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.proto import plaso_storage_pb2

MAX_INT64 = 2**64-1
__version__ = '1.0'


def GetMicroseconds(date_str, timezone):
  """Returns microseconds from epoch for a given date string and pytz timezone.

  Args:
    date_str: YYYY-MM-DD HH:MM:SS
    timezone: pytz timezone object of the timezone of this time. (e.g. Eastern)

  Returns:
    Integer of microseconds from epoch.
  """

  dt = dateutil.parser.parse(date_str)
  loc_dt = timezone.localize(dt)
  utc_dt = loc_dt.astimezone(pytz.UTC)
  # 1e6 = 1,000,000 is the multiple to convert seconds to microseconds.
  return calendar.timegm(utc_dt.timetuple()) * int(1e6)


def GetTimes(my_args):
  """Returns first and last in microseconds from user supplied flags.

  There are two ways (microseconds and human readable YYYY-MM-DD HH:MM:SS) to
  define time on the input line.  This function determines which was used and
  returns the approriate pair.

  Returns:
    (first, last): First and last timestamp as microseconds.
  """
  # TODO: Write logic to intake (seconds, microseconds, or human friendly)
  # dates with one flag instead of two.

  timezone = pytz.timezone(my_args.timezone)
  if my_args.first_time:
    first = GetMicroseconds(my_args.first_time, timezone)
  else:
    first = my_args.first_time_microsec
  if my_args.last_time:
    last = GetMicroseconds(my_args.last_time, timezone)
  else:
    last = my_args.last_time_microsec
  return first, last


def SetupStorage(input_file_path):
  """Sets up the storage object.

  Attempts to initialize the storage object from the PlasoStorage library.  If
  we fail on a IO Error (common case for typos) log a warning and gracefully
  exit.

  Args:
    input_file_path: Filesystem path to the plaso storage container.

  Returns:
    A storage.PlasoStorage object.
  """
  try:
    return storage.PlasoStorage(input_file_path, read_only=True)
  except IOError as details:
    logging.error('IO ERROR: %s', details)
  else:
    logging.error('Other Critical Failure Reading Files')
  sys.exit(1)


def ReadMeta(store, bound_first, bound_last):
  """Yields container nums that have events in the given time bounds.

  This function reads the meta data file from Plaso Storage Containers.  Meta
  data wasn't introduced until version 1.  Lack of meta data is not a critical
  failure but will add to total processing time because we can't filter out
  non-matching containers.  For containers lacking meta data default values will
  be supplied for them.

  Note: Version number is also part of meta_data but since this is version 1
  there is nothing to do with this yet.

  Args:
    store: A storage.PlasoStorage object.
    bound_first: Earliest microsecond considered in bounds.
    bound_last: Latest microsecond considered in bounds.

  Yields:
    The number of a container when entries in it are within time boundries.
  """
  for number in store.GetProtoNumbers():
    first, last = store.ReadMeta(number).get('range', (0, MAX_INT64))
    if first == 0:
      logging.info('Assuming container %s starts from time 0.',
                   number)
    if last == MAX_INT64:
      logging.info('Inserting default last timestamp for container %s.',
                   number)
    if last < first:
      logging.error('last: %d first: %d container: %d (last < first)',
                    last, first, number)
      sys.exit(1)
    if first <= bound_last and bound_first <= last:
      yield number


def ReadPbCheckTime(number, bound_first, bound_last, output_renderer):
  """Returns a plaso storage PB object whose timestamp is within time bounds.

  Args:
    number: Container number.
    bound_first: Earliest microsecond considered in bounds.
    bound_last: Latest microsecond considered in bounds.
    output_renderer: The output renderer used.

  Returns:
    If in bound (storage object item timestamp, full storage proto object).

    or

    (None, None) if there are no more protos or they are out of bounds.
  """

  while True:
    proto_read = output_renderer.FetchEntry(number)
    if not proto_read:
      return None, None

    elif bound_first <= proto_read.timestamp <= bound_last:
      return proto_read.timestamp, proto_read


def MergeSort(range_checked_nums, bound_first, bound_last, my_output,
              my_filter=None):
  """Performs an external merge sort of the events and sends them to output.

  Args:
    range_checked_nums: Container numbers with relevant entries.
    bound_first: Earliest microsecond considered in bounds.
    bound_last: Latest microsecond considered in bounds.
    my_output: OutputRenderer object.
    my_filter: A filter string.

  """
  read_list = []

  matcher = None
  filter_count = 0
  if my_filter:
    matcher = pfilter.GetMatcher(my_filter)
    if not matcher:
      logging.error('Filter malformed, exiting.')
      sys.exit(1)

  for proto_file_number in range_checked_nums:
    timestamp, storage_proto = ReadPbCheckTime(
        proto_file_number, bound_first, bound_last, my_output)
    heapq.heappush(read_list, (timestamp, proto_file_number, storage_proto))

  while read_list:
    timestamp, file_number, event_read = heapq.heappop(read_list)
    if not event_read:
      continue
    if not matcher:
      my_output.Append(event_read)
    else:
      event_match = event_read
      if isinstance(event_read, plaso_storage_pb2.EventObject):
        event_match = event.EventObject()
        event_match.FromProto(event_read)

      if matcher.Matches(event_match):
        my_output.Append(event_read)
      else:
        filter_count += 1
    new_timestamp, new_event_read = ReadPbCheckTime(
        file_number, bound_first, bound_last, my_output)
    if new_event_read:
      heapq.heappush(read_list, (new_timestamp, file_number, new_event_read))

  my_output.Flush()
  if filter_count:
    logging.info('Events filtered out: %d', filter_count)


class OutputRenderer(object):
  """This class handles output and formating.

     Currently only supports dumping basic to string formating of objects.
  """

  def __init__(self, store, out_format='L2tcsv', timezone='UTC',
               file_descriptor=sys.stdout):
    """Initalizes the OutputRenderer.

    Args:
      store: The storage object (PlasoStorage).
      out_format:  Name of output_lib formatter class to use.
      timezone: The timezone of the output
      file_descriptor:  File descriptor to send output to.
    """
    self.buffer_list = []
    format_str = '%s%s' % (out_format[0].upper(), out_format[1:].lower())

    # TODO: out_format should check against loaded output modules and help the
    # user find the right one with output_lib.ListOutputFormatters().
    try:
      self.formatter = (
          output_lib.LogOutputFormatter.classes[format_str](
              store, file_descriptor, pytz.timezone(timezone)))
      self.formatter.Start()  # Write header
    except IOError as e:
      logging.error('Error occured during output processing: %s', e)
      self.formatter = None

  def Append(self, mblog):
    """Adds a record to the output buffer.

    Currently immediately calls Flush.  Will be changed when De-Dupe is
    implemented.

    Args:
      mblog: tuple of (evt timestamp, protobuf, container number).
    """
    # TODO: Perform de-duplication of records.  The source input files may
    # contain duplicates and that may not add additional value.  DeDupe is
    # complicated will deal with that in the next version.

    self.buffer_list.append(mblog)
    self.Flush()

  def FetchEntry(self, store_number):
    """Fetch an entry from the store."""
    return self.formatter.FetchEntry(store_number)

  def Flush(self):
    """Flushes the buffer by sending records to a formatter and prints."""
    while self.buffer_list:
      self.formatter.WriteEvent(self.buffer_list.pop(0))

  def End(self):
    """Call the formatter to produce the closing line."""
    if self.formatter:
      self.formatter.End()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


def Main():
  """Start the tool."""
  parser = argparse.ArgumentParser(
      description='Psort (Plaso Síar Og Raðar Þessu) - Human-readable from'
      ' PlasoStorage files.')

  parser.add_argument('-d', '--debug', action='store_true',
                      help='Fall back to debug shell if psort fails.')

  parser.add_argument('-t', '--first_time', metavar='STARTDATE',
                      dest='first_time', help='Earliest time as "YYYY-MM-DD'
                      'HH:MM:SS"')

  parser.add_argument('-tus', '--first_time_microsec',
                      metavar='FIRSTTIMESTAMP_USEC', dest='first_time_microsec',
                      default=0, type=int,
                      help='Earliest time as a microsecond')

  parser.add_argument('-T', '--last_time', metavar='ENDDATE', dest='last_time',
                      help='Last time as "YYYY-MM-DD HH:MM:SS"')

  parser.add_argument('-Tus', '--last_time_microsec',
                      metavar='LASTIMESTAMP_USEC',
                      dest='last_time_microsec', default=MAX_INT64, type=int,
                      help='Latest time as microsecond.')

  parser.add_argument('-o', '--output_format', metavar='FORMAT',
                      dest='output_format', default='L2tCsv',
                      help='Output format.  -o list to see loaded modules.')

  parser.add_argument('-z', '--zone', metavar='TIMEZONE', default='UTC',
                      dest='timezone',
                      help='Timezone of output. list: "-z list"')

  parser.add_argument('-w', '--write', metavar='OUTPUTFILE', dest='write',
                      help='Output filename.  Defaults to stdout.')

  parser.add_argument('-v', '--version', dest='version', action='version',
                      version='log2timeline - psort version %s' % __version__,
                      help='Show the current version of psort.')

  parser.add_argument('storagefile', metavar='PLASOFILE', default=None,
                      nargs='?', help='Path to the Plaso storage file')

  parser.add_argument(
      'filter', nargs='?', action='store', metavar='FILTER', default=None,
      help=('A filter that can be used to filter the dataset before it '
            'is written into storage. More information about the filters'
            ' and it\'s usage can be found here: http://plaso.kiddaland.'
            'net/usage/filters'))

  my_args = parser.parse_args()

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  if my_args.timezone == 'list':
    print '=' * 40
    print '       ZONES'
    print '-' * 40
    for zone in pytz.all_timezones:
      print '  %s' % zone
    print '=' * 40
    sys.exit(0)

  if my_args.output_format == 'list':
    print '=' * 40
    print '       FORMATTERS'
    print '-' * 40
    for name, description in output_lib.ListOutputFormatters():
      print '%s -  %s' % (name, description)
    print '=' * 40
    sys.exit(0)

  if not my_args.storagefile:
    parser.print_help()
    print ''
    parser.print_usage()
    print ''
    logging.error('STORAGEFILE required! or -h for HELP')
    sys.exit(0)

  first, last = GetTimes(my_args)

  if not my_args.write:
    my_args.write = sys.stdout

  with SetupStorage(my_args.storagefile) as store:
    # Identify Files
    range_checked_pb_nums = ReadMeta(store, first, last)
    with OutputRenderer(store, my_args.output_format, my_args.timezone,
                        my_args.write) as output_render:
      if output_render.formatter:
        try:
          MergeSort(range_checked_pb_nums, first, last,
                    output_render, my_args.filter)
        # Catching a very generic error in case we would like to debug
        # a potential crash in the tool.
        except Exception:
          if not my_args.debug:
            raise
          pdb.post_mortem()


if __name__ == '__main__':
  Main()
