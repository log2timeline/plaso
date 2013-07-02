#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Plasm (Plaso Langar Að Safna Minna) - Groups and tags Plaso Storage files.

Plasm is used to apply Tags and Groups to the Plaso Storage file.

When applying tags, a tag input file must be given. Currently, the format of
this file is simply the tag name, followed by indented lines indicating
conditions for the tag, treating any lines beginning with # as comments. For
example, a valid tagging input file might look like this:

------------------------------
Obvious Malware
  # anything with 'malware' in the name or path
  filename contains 'malware'

  # anything with the malware datatype
  datatype is 'windows:malware:this_is_not_a_real_datatype'

File Download
  timestamp_desc is 'File Downloaded'
------------------------------

When applying groups, the Plaso Storage file *must* contain tags, as only tagged
events are grouped. Plasm can be run such that it both applies tags and applies
groups, in which case an untagged Plaso Storage file may be used, since tags
will be applied before the grouping is calculated.

Sample Usage:
  plasm.py --tag tag_input.txt -g /tmp/storage.dump"""
import argparse
import logging
import os
import sys

from plaso import filters   # pylint: disable-msg=W0611

from plaso.lib import event
from plaso.lib import filter_interface
from plaso.lib import storage


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
    return storage.PlasoStorage(input_file_path, read_only=False)
  except IOError as details:
    logging.error('IO ERROR: %s', details)
  else:
    logging.error('Other Critical Failure Reading Files')
  sys.exit(1)


def EventObjectGenerator(plaso_storage, quiet=False):
  """Yields EventObject objects.

  Yields event_objects out of a PlasoStorage object. If the 'quiet' argument
  is not present, it also outputs 50 '.'s indicating progress.

  Args:
    plaso_storage: a storage.PlasoStorage object.
    quiet: boolean value indicating whether to suppress progress output.

  Yields:
    EventObject objects.
  """

  if not quiet:
    total_events = 0
    if hasattr(plaso_storage, 'GetInformation'):
      for store_info in plaso_storage.GetInformation():
        if hasattr(store_info, 'stores'):
          stores = store_info.stores.values()
          for store_file in stores:
            if type(store_file) is dict and 'count' in store_file:
              total_events += store_file['count']
    if total_events > 0:
      events_per_dot = total_events // 50
      counter = 0
    else:
      quiet = True

  event_object = plaso_storage.GetSortedEntry()
  while event_object:
    if not quiet:
      counter += 1
      if counter % events_per_dot == 0:
        sys.stdout.write('.')
        sys.stdout.flush()
    yield event_object
    event_object = plaso_storage.GetSortedEntry()


def ParseTaggingFile(tag_input):
  """Parses Tagging Input file.

  Parses a tagging input file and returns a dictionary of tags, where each
  key represents a tag and each entry is a list of plaso filters

  Args:
    tag_input: Filesystem path to the tagging input file.

  Returns:
    A dictionary whose keys are tags and values are EventObjectFilter objects.
  """

  with open(tag_input, 'rb') as tag_input_file:
    tags = {}
    current_tag = ''
    for line in tag_input_file:
      line_rstrip = line.rstrip()
      line_strip = line_rstrip.lstrip()
      if not line_strip or line_strip.startswith("#"):
        continue
      if not line_rstrip[0].isspace():
        current_tag = line_rstrip
        tags[current_tag] = []
      else:
        if not current_tag:
          continue
        compiled_filter = filter_interface.GetFilter(line_strip)
        if compiled_filter:
          if compiled_filter not in tags[current_tag]:
            tags[current_tag].append(compiled_filter)
        else:
          logging.warning(u'Tag "{}" contains invalid filter: {}'.format(
              current_tag, line_strip))
  return tags


def TaggingEngine(my_args):
  """Applies tags to the plaso store.

  Iterates through a Plaso Store file, tagging events according to the
  tagging input file specified on the command line. It writes the tagging
  information to the Plaso Store file.

  Args:
    my_args: configuration object containing at least 'storagefile' and
             'tag_input' properties.
"""

  if not my_args.quiet:
    sys.stdout.write('Applying tags...\n')
  with SetupStorage(my_args.storagefile) as store:
    tags = ParseTaggingFile(my_args.tag_input)
    num_tags = 0
    event_tags = []
    for event_object in EventObjectGenerator(store, my_args.quiet):
      matched_tags = []
      for tag, my_filters in tags.items():
        for my_filter in my_filters:
          if my_filter.Match(event_object):
            matched_tags.append(tag)
      if len(matched_tags) > 0:
        event_tag = event.EventTag()
        event_tag.store_number = getattr(event_object, 'store_number')
        event_tag.store_index = getattr(event_object, 'store_index')
        event_tag.comment = 'Tag applied by PLASM tagging engine'
        event_tag.tags = matched_tags
        event_tags.append(event_tag)
        num_tags += 1
    store.StoreTagging(event_tags)

  if not my_args.quiet:
    sys.stdout.write('DONE (applied {} tags)\n'.format(num_tags))


def GroupingEngine(my_args):
  """Applies groups to the plaso store.

  Iterates through a tagged Plaso Store file, grouping events with the same
  tag into groups indicating a single instance of an action. It writes the
  grouping information to the Plaso Store file.

  Args:
    my_args: configuration object containing at least 'storagefile' property.

  """

  if not my_args.quiet:
    sys.stdout.write('Grouping tagged events...\n')
  # We re-open the storeagefile so that -t and -g can happen on the same run.
  with SetupStorage(my_args.storagefile) as store:
    if not store.HasTagging():
      logging.error('Plaso storage file does not contain tagged events')
      return
    # Reformat tags as "tag name" => [event, ...]
    all_tags = {}
    for event_tag in store.GetTagging():
      tags = event_tag.tags
      location = (event_tag.store_number, event_tag.store_index)
      for tag in tags:
        if tag in all_tags:
          all_tags[tag].append(location)
        else:
          all_tags[tag] = [location]
    # Separate each tag list into groups.
    # TODO(ojensen): make this smarter - for now, separates via time interval.
    time_interval = 1000000  # 1 second.
    groups = []
    for tag in all_tags:
      if not my_args.quiet:
        sys.stdout.write(u'  proccessing tag "{}"...\n'.format(tag))
      locations = all_tags[tag]
      last_time = 0
      groups_in_tag = 0
      for location in locations:
        store_number, store_index = location
        # TODO(ojensen): getting higher number event_objects seems to be slow.
        event_object = store.GetEntry(store_number, store_index)
        if not hasattr(event_object, 'timestamp'):
          continue
        timestamp = getattr(event_object, 'timestamp')
        if timestamp - last_time > time_interval:
          groups_in_tag += 1
          groups.append(type('obj', (object,), {
              'name': u'{}:{}'.format(tag, groups_in_tag),
              'category': tag,
              'events': [location]}))
        else:
          groups[-1].events.append(location)
        last_time = timestamp
    # Store this group in the plaso storage.
    store.StoreGrouping(groups)

  if not my_args.quiet:
    sys.stdout.write('DONE\n')


def Main():
  """Start the tool."""
  parser = argparse.ArgumentParser(
      description=(
          u'PLASM (...) - Group, tag and cluster output from a plaso storage '
          'file'))

  parser.add_argument(
      'storagefile', metavar='PLASOFILE', default=None, nargs='?',
      help='Path to the Plaso storage file')

  parser.add_argument(
      '-t', '--tag', metavar='FILE', dest='tag_input',
      help='Tagging input file (ascii protobuff).')

  parser.add_argument(
      '-g', '--group', action='store_true', dest='group', default=False,
      help='Group tagged elements into individual instances of events.')

  parser.add_argument(
      '-q', '--quiet', action='store_true', dest='quiet', default=False,
      help='Minimize output')

  my_args = parser.parse_args()

  if not my_args.storagefile:
    parser.print_help()
    print ''
    parser.print_usage()
    print ''
    logging.error('STORAGEFILE required! or -h for HELP')
    sys.exit(0)

  if my_args.tag_input:
    if not os.path.isfile(my_args.tag_input):
      parser.print_help()
      print ''
      parser.print_usage()
      print ''
      logging.error(u'Tagging input file {} does not exist.'.format(
          my_args.tag_input))
      sys.exit(0)
    TaggingEngine(my_args)

  if my_args.group:
    GroupingEngine(my_args)


if __name__ == '__main__':
  Main()
