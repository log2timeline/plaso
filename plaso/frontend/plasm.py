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
"""This file contains the plasm front-end to plaso."""

import argparse
import hashlib
import logging
import operator
import os
import pickle
import sets
import sys
import textwrap

from plaso import filters

from plaso.lib import event
from plaso.lib import output as output_lib
from plaso.lib import storage

# pylint: disable-msg=unused-import
from plaso.output import pstorage


def SetupStorage(input_file_path, pre_obj=None):
  """Sets up the storage object.

  Attempts to initialize a storage file. If we fail on a IOError, for which
  a common cause are typos, log a warning and gracefully exit.

  Args:
    input_file_path: Filesystem path to the plaso storage container.
    pre_obj: A plaso preprocessing object.

  Returns:
    A storage.StorageFile object.
  """
  try:
    return storage.StorageFile(
        input_file_path, pre_obj=pre_obj, read_only=False)
  except IOError as details:
    logging.error('IO ERROR: %s', details)
  else:
    logging.error('Other Critical Failure Reading Files')
  sys.exit(1)


def EventObjectGenerator(plaso_storage, quiet=False):
  """Yields EventObject objects.

  Yields event_objects out of a StorageFile object. If the 'quiet' argument
  is not present, it also outputs 50 '.'s indicating progress.

  Args:
    plaso_storage: a storage.StorageFile object.
    quiet: boolean value indicating whether to suppress progress output.

  Yields:
    EventObject objects.
  """

  total_events = plaso_storage.GetNumberOfEvents()
  if total_events > 0:
    events_per_dot = operator.floordiv(total_events, 80)
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
  key represents a tag and each entry is a list of plaso filters.

  Args:
    tag_input: filesystem path to the tagging input file.

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
        compiled_filter = filters.GetFilter(line_strip)
        if compiled_filter:
          if compiled_filter not in tags[current_tag]:
            tags[current_tag].append(compiled_filter)
        else:
          logging.warning(u'Tag "{}" contains invalid filter: {}'.format(
              current_tag, line_strip))
  return tags


class TaggingEngine(object):
  """Applies tags to the plaso store."""
  def __init__(self, target_filename, tag_input, quiet=False):
    """Constructor for the Tagging Engine.

    Args:
      target_filename: filename for a Plaso storage file to be tagged.
      tag_input: filesystem path to the tagging input file.
      quiet: suppress the progress output (default: False).
    """
    self.target_filename = target_filename
    self.tag_input = tag_input
    self.quiet = quiet

  def Run(self):
    """Iterates through a Plaso Store file, tagging events according to the
    tagging input file specified on the command line. It writes the tagging
    information to the Plaso Store file."""
    pre_obj = event.PreprocessObject()
    pre_obj.collection_information = {}
    pre_obj.collection_information['file_processed'] = self.target_filename
    pre_obj.collection_information['method'] = 'Applying tags.'
    pre_obj.collection_information['tag_file'] = self.tag_input
    pre_obj.collection_information['tagging_engine'] = 'plasm'

    if not self.quiet:
      sys.stdout.write('Applying tags...\n')
    with SetupStorage(self.target_filename, pre_obj) as store:
      tags = ParseTaggingFile(self.tag_input)
      num_tags = 0
      event_tags = []
      for event_object in EventObjectGenerator(store, self.quiet):
        matched_tags = []
        for tag, my_filters in tags.iteritems():
          for my_filter in my_filters:
            if my_filter.Match(event_object):
              matched_tags.append(tag)
              # Don't want to evaluate other tags once a tag is discovered.
              break
        if len(matched_tags) > 0:
          event_tag = event.EventTag()
          event_tag.store_number = getattr(event_object, 'store_number')
          event_tag.store_index = getattr(event_object, 'store_index')
          event_tag.comment = 'Tag applied by PLASM tagging engine'
          event_tag.tags = matched_tags
          event_tags.append(event_tag)
          num_tags += 1
      store.StoreTagging(event_tags)

    if not self.quiet:
      sys.stdout.write('DONE (applied {} tags)\n'.format(num_tags))


class GroupingEngine(object):
  """Applies groups to the plaso store."""

  def __init__(self, target_filename, quiet=False):
    """Constructor for the Grouping Engine.

    Args:
      target_filename: filename for a Plaso storage file to be tagged.
      quiet: suppress the progress output (default: False).
    """
    self.target_filename = target_filename
    self.quiet = quiet

  @staticmethod
  def ReadTags(store):
    """Iterates through an opened Plaso Store, creating a dictionary of tags
    pointing to a list of events.

    Args:
      store: initialized Plaso Store.
    """
    all_tags = {}
    for event_tag in store.GetTagging():
      tags = event_tag.tags
      location = (event_tag.store_number, event_tag.store_index)
      for tag in tags:
        if tag in all_tags:
          all_tags[tag].append(location)
        else:
          all_tags[tag] = [location]
    return all_tags

  @staticmethod
  def GroupEvents(store, tags, quiet=False):
    """Separates each tag list into groups, and writes them to the Plaso Store.

    Args:
      store: initialized Plaso Store.
      tags: dictionary of the form {tag: [event_object, ...]}.
      quiet: suppress the progress output (default: False).
    """
    # TODO(ojensen): make this smarter - for now, separates via time interval.
    time_interval = 1000000  # 1 second.
    groups = []
    for tag in tags:
      if not quiet:
        sys.stdout.write(u'  proccessing tag "{}"...\n'.format(tag))
      locations = tags[tag]
      last_time = 0
      groups_in_tag = 0
      for location in locations:
        store_number, store_index = location
        # TODO(ojensen): getting higher number event_objects seems to be slow.
        event_object = store.GetEventObject(store_number, store_index)
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
    return groups

  def Run(self):
    """Iterates through a tagged Plaso Store file, grouping events with the same
    tag into groups indicating a single instance of an action. It writes the
    grouping information to the Plaso Store file."""

    if not self.quiet:
      sys.stdout.write('Grouping tagged events...\n')
    with SetupStorage(self.target_filename) as store:
      if not store.HasTagging():
        logging.error('Plaso storage file does not contain tagged events')
        return
      tags = GroupingEngine.ReadTags(store)
      groups = GroupingEngine.GroupEvents(store, tags, self.quiet)
      store.StoreGrouping(groups)
    if not self.quiet:
      sys.stdout.write('DONE\n')


class ClusteringEngine(object):
  """Clusters events in a Plaso Store to assist Tag Input creation.

  Most methods in this class are staticmethods, to avoid relying excessively on
  internal state, and to maintain a clear description of which method acts on
  what data.
  """

  IGNORE_BASE = frozenset(['hostname', 'timestamp_desc', 'plugin',
      'parser', 'user_sid', 'registry_type', 'computer_name', 'offset',
      'allocated', 'file_size', 'record_number'])

  def __init__(self, target_filename, threshold, closeness):
    """Constructor for the Clustering Engine.

    Args:
      target_filename: filename for a Plaso storage file to be clustered.
      threshold: support threshold for pruning attributes and event types.
      closeness: number of miliseconds to cut off the closeness function.
    """
    self.target_filename = target_filename
    self.threshold = threshold
    self.closeness = closeness
    sys.stdout.write("Support threshold: {}\nCloseness: {}ms\n\n".format(
      threshold, closeness))

    self.ignore = False
    self.frequent_words = []
    self.vector_size = 20000

  @staticmethod
  def HashFile(filename, block_size=2**20):
    """Calculates an md5sum of a file from a given filename.

    Returns an MD5 (hash) in ASCII characters, used for naming incremental
    progress files that are written to disk.

    Args:
      filename: the file to be hashed.
      block_size: (optional) block size.
    """
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
      while True:
        data = f.read(block_size)
        if not data:
          break
        md5.update(data)
    return md5.hexdigest()

  @staticmethod
  def StringJoin(first, second):
    """Joins two strings together with a separator.

    In spite of being fairly trivial, this is separated out as a function of
    its own to ensure it stays consistent, as it happens in multiple places in
    the code.

    Args:
      first: first string.
      second: second string.
    """
    return ':||:'.join([unicode(first), unicode(second)])

  @staticmethod
  def PreHash(field_name, attribute):
    """Constructs a string fit to be hashed from an event_object attribute.

    Takes both the attribute's name and value, and produces a consistent string
    representation. This string can then be hashed to produce a consistent
    name/value hash (see hash_attr).

    Args:
      field_name: an event_object attribute name.
      attribute: the corresponding event_object attribute.
    """
    if type(attribute) in [dict, sets.Set]:
      value = repr(sorted(attribute.items()))
    else:
      value = unicode(attribute)
    return ClusteringEngine.StringJoin(field_name, value)

  @staticmethod
  def HashAttr(field_name, attribute, vector_size):
    """Consistently hashes an event_object attribute/value pair.

    Uses pre_hash to generate a consistent string representation of the
    attribute, and then hashes and mods it down to fit within the vector_size.

    Args:
      field_name: an event_object attribute name.
      attribute: the corresponding event_object attribute.
    """
    return hash(ClusteringEngine.PreHash(field_name, attribute)) % vector_size

  @staticmethod
  def EventRepresentation(event_object, ignore, frequent_words=None):
    """Constructs a consistent representation of an event_object.

    Returns a dict representing our view of an event_object, stripping out
    attributes we ignore. If the frequent_words parameter is set, this strips
    out any attribute not listed therein as well. Attribute list order is
    undefined, i.e. event_object list attributes are treated as sets instead of
    lists.

    Args:
      event_object: a Plaso event_object.
      ignore: a list or set of event_object attributes to ignore.
      frequent_words: (optional) whitelist of attributes not to ignore.
    """
    if not frequent_words:
      frequent_words = []

    event_field_names = event_object.GetAttributes().difference(ignore)
    representation = {}
    for field_name in event_field_names:
      attribute = getattr(event_object, field_name)
      if hasattr(attribute, '__iter__'):
        if isinstance(attribute, dict):
          indeces = sorted(attribute.keys())
        else:
          indeces = range(len(attribute))
        for index in indeces:
          # quick fix to ignore list order.
          index_identifier = index if isinstance(attribute, dict) else ''
          subfield_name = ':plasm-sub:'.join(
              [field_name, unicode(index_identifier)])
          if not frequent_words or ClusteringEngine.StringJoin(
              subfield_name, attribute[index]) in frequent_words:
            representation[subfield_name] = attribute[index]
      else:
        if not frequent_words or ClusteringEngine.StringJoin(
            field_name, attribute) in frequent_words:
          representation[field_name] = attribute
    return representation

  def EventObjectRepresentationGenerator(self, filename, frequent_words=None):
    """Yields event_representations.

    Yields event_representations from a plaso store. Essentially it simply wraps
    the EventObjectGenerator and yields event_representations of the resulting
    event_objects. If frequent_words is set, the event representation will
    exclude any attributes not listed in the frequent_words list.

    Args:
      filename: a Plaso Store filename.
      frequent_words: (optional) whitelist of attributes not to ignore.
    """
    with SetupStorage(filename) as store:
      for event_object in EventObjectGenerator(store):
        if not self.ignore:
          self.ignore = event_object.COMPARE_EXCLUDE.union(self.IGNORE_BASE)
        yield ClusteringEngine.EventRepresentation(
            event_object, self.ignore, frequent_words)

  def NoDuplicates(self, dump_filename):
    """Saves a de-duped Plaso Storage.

    This goes through the Plaso storage file, and saves a new dump with
    duplicates removed. The filename is '.[dump_hash]_dedup', and is returned
    at the end of the function. Note that if this function is interrupted,
    incomplete results are recorded and this file must be deleted or subsequent
    runs will use this incomplete data.

    Args:
      dump_filename: the filename of the Plaso Storage to be deduped.
    """
    sys.stdout.write('Removing duplicates...\n')
    sys.stdout.flush()
    # Whether these incremental files should remain a feature or not is still
    # being decided. They're just here for now to make development faster.
    nodup_filename = '.{}_dedup'.format(self.plaso_hash)
    if os.path.isfile(nodup_filename):
      sys.stdout.write('Using previously calculated results.\n')
    else:
      with SetupStorage(dump_filename) as store:
        total_events = store.GetNumberOfEvents()
        events_per_dot = operator.floordiv(total_events, 80)
        formatter_cls = output_lib.GetOutputFormatter('Pstorage')
        store_dedup = open(nodup_filename, 'wb')
        formatter = formatter_cls(store, store_dedup)
        with output_lib.EventBuffer(
            formatter, check_dedups=True) as output_buffer:
          event_object = formatter.FetchEntry()
          counter = 0
          while event_object:
            output_buffer.Append(event_object)
            counter += 1
            if counter % events_per_dot == 0:
              sys.stdout.write('.')
              sys.stdout.flush()
            event_object = formatter.FetchEntry()
      sys.stdout.write ('\n')
    return nodup_filename

  def ConstructHashVector(self, nodup_filename, vector_size):
    """Constructs the vector which tallies the hashes of attributes.

    The purpose of this vector is to save memory. Since many attributes are
    fairly unique, we first hash them and keep a count of how many times the
    hash appears. Later when constructing our vocabulary, we can ignore any
    attributes whose hash points to a value in this vector smaller than the
    support threshold value, since we are guaranteed that it appears in the
    data at most this tally number of times.

    Args:
      nodup_filename: the filename of a de-duplicated plaso storage file.
      vector_size: size of this vector.
    """
    sys.stdout.write('Constructing word vector...\n')
    sys.stdout.flush()
    vector_filename = '.{}_vector_{}'.format(
        self.plaso_hash, vector_size)
    if os.path.isfile(vector_filename):
      sys.stdout.write('Using previously calculated results.\n')
      x = open(vector_filename, 'rb')
      vector = pickle.load(x)
      x.close()
    else:
      vector = [0]*vector_size
      for representation in self.EventObjectRepresentationGenerator(
          nodup_filename):
        for field_name, attribute in representation.iteritems():
          index = ClusteringEngine.HashAttr(field_name, attribute, vector_size)
          vector[index] += 1
      x = open(vector_filename, 'wb')
      pickle.dump(vector, x)
      x.close()
      sys.stdout.write('\n')
    return vector

  def FindFrequentWords(self, nodup_filename, threshold, vector=None):
    """Constructs a list of attributes which appear "often".

    This goes through a plaso store, and finds all name-attribute pairs which
    appear no less than the support threshold value number of times. If
    available it uses the hash vector in order to ignore attributes and save
    memory.

    Args:
      nodup_filename: the filename of a de-duplicated plaso storage file.
      threshold: the support threshold value.
      vector: (optional) vector of hash tallies.
    """
    if not vector:
      vector = []

    sys.stdout.write('Constructing 1-dense clusters... \n')
    sys.stdout.flush()
    frequent_filename = '.{}_freq_{}'.format(self.plaso_hash,
        str(threshold))
    if os.path.isfile(frequent_filename):
      sys.stdout.write('Using previously calculated results.\n')
      x = open(frequent_filename, 'rb')
      frequent_words = pickle.load(x)
      x.close()
    else:
      word_count = {}
      vector_size = len(vector)
      for representation in self.EventObjectRepresentationGenerator(
          nodup_filename):
        for field_name, attribute in representation.iteritems():
          word = ClusteringEngine.PreHash(field_name, attribute)
          keep = vector[hash(word) % vector_size] > threshold
          if not vector_size or keep:
            if word in word_count:
              word_count[word] += 1
            else:
              word_count[word] = 1
      wordlist = [word for word in word_count if word_count[word] >= threshold]
      frequent_words = sets.Set(wordlist)
      x = open(frequent_filename, 'wb')
      pickle.dump(frequent_words, x)
      x.close()
      sys.stdout.write('\n')
    return frequent_words

  def BuildEventTypes(self, nodup_filename, threshold, frequent_words):
    """Builds out the event_types from the frequent attributes.

    This uses the frequent words set in order to ignore attributes from plaso
    events and thereby create event_types (events which have infrequent
    attributes ignored). Currently event types which do not appear at least
    as ofter as the support threshold dictates are ignored, although whether
    this is what we actually want is still under consideration. Returns the
    list of event types, as well as a reverse-lookup structure.

    Args:
      nodup_filename: the filename of a de-duplicated plaso storage file.
      threshold: the support threshold value.
      frequent_words: the set of attributes not to ignore.
    """
    sys.stdout.write('Calculating event type candidates...\n')
    sys.stdout.flush()
    eventtype_filename = ".{}_evtt_{}".format(self.plaso_hash,
        str(threshold))
    if os.path.isfile(eventtype_filename):
      sys.stdout.write('Using previously calculated results.\n')
      x = open(eventtype_filename, 'rb')
      evttypes = pickle.load(x)
      evttype_indeces = pickle.load(x)
      x.close()
    else:
      evttype_candidates = {}
      for representation in self.EventObjectRepresentationGenerator(
          nodup_filename, frequent_words=frequent_words):
        candidate = repr(representation)
        if candidate in evttype_candidates:
          evttype_candidates[candidate] += 1
        else:
          evttype_candidates[candidate] = 1
      sys.stdout.write('\n')
      # clean up memory a little
      sys.stdout.write('Pruning event type candidates...')
      sys.stdout.flush()
      evttypes = []
      evttype_indeces = {}
      for candidate, score in evttype_candidates.iteritems():
        if score < threshold:
          evttype_indeces[candidate] = len(evttypes)
          evttypes.append(candidate)
      del(evttype_candidates)
      # write everything out
      x = open(eventtype_filename, 'wb')
      pickle.dump(evttypes, x)
      pickle.dump(evttype_indeces, x)
      x.close()
      sys.stdout.write('\n')
    return (evttypes, evttype_indeces)

  def Run(self):
    """Iterates through a tagged Plaso Store file, attempting to cluster events
    into groups that tend to happen together, to help creating Tag Input files.
    Future work includes the ability to parse multiple Plaso Store files at
    once. By default this will write incremental progress to dotfiles in the
    current directory."""
    self.plaso_hash = ClusteringEngine.HashFile(self.target_filename)
    self.nodup_filename = self.NoDuplicates(self.target_filename)
    self.vector = self.ConstructHashVector(
        self.nodup_filename, self.vector_size)
    self.frequent_words = self.FindFrequentWords(
        self.nodup_filename, self.threshold, self.vector)
    (self.event_types, self.event_type_indeces) = self.BuildEventTypes(
        self.nodup_filename, self.threshold, self.frequent_words)
    # Next step, clustering the event types
    # TODO(ojensen): clustering


def Main():
  """The main application function."""
  epilog_tag = ("""
      Notes:

      When applying tags, a tag input file must be given. Currently,
      the format of this file is simply the tag name, followed by
      indented lines indicating conditions for the tag, treating any
      lines beginning with # as comments. For example, a valid tagging
      input file might look like this:'

      ------------------------------
      Obvious Malware
          # anything with 'malware' in the name or path
          filename contains 'malware'

          # anything with the malware datatype
          datatype is 'windows:malware:this_is_not_a_real_datatype'

      File Download
          timestamp_desc is 'File Downloaded'
      ------------------------------
      """)

  epilog_group = ("""
      When applying groups, the Plaso storage file *must* contain tags,
      as only tagged events are grouped. Plasm can be run such that it
      both applies tags and applies groups, in which case an untagged
      Plaso storage file may be used, since tags will be applied before
      the grouping is calculated.
      """)

  description = (
      u'PLASM (Plaso Langar Ad Safna Minna)- Application to group and tag '
      u'Plaso storage files.')

  argument_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description),
      formatter_class=argparse.RawDescriptionHelpFormatter)

  argument_parser.add_argument(
      '-q', '--quiet', action='store_true', dest='quiet', default=False,
      help='Suppress nonessential output.')

  subparsers = argument_parser.add_subparsers(dest='subcommand')

  cluster_subparser = subparsers.add_parser(
      'cluster', formatter_class=argparse.RawDescriptionHelpFormatter)

  cluster_subparser.add_argument(
      '--closeness', action='store', type=int, metavar='MSEC',
      dest='cluster_closeness', default=5000, help=(
          'Number of miliseconds before we stop considering two '
          'events to be at all "close" to each other'))

  cluster_subparser.add_argument(
      '--threshold', action='store', type=int, metavar='NUMBER',
      dest='cluster_threshold', default=5,
      help='Support threshold for pruning attributes.')

  cluster_subparser.add_argument(
      'storage_file', action='store', type=unicode, metavar='STORAGE_FILE',
      nargs='?', help=(
          'The path to the storage file, if the file exists data will '
          'get appended to it.'))

  subparsers.add_parser(
      'group', formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog_group))

  tag_subparser = subparsers.add_parser(
      'tag', formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog_tag))

  tag_subparser.add_argument(
      '--tagfile', action='store', type=unicode, metavar='FILE',
      dest='tag_filename', help=(
          'Name of the file containing a description of tags and rules '
          'for tagging events.'))

  tag_subparser.add_argument(
      'storage_file', action='store', type=unicode, metavar='STORAGE_FILE',
      nargs='?', help=(
          'The path to the storage file, if the file exists data will '
          'get appended to it.'))

  arguments = argument_parser.parse_args()

  if not os.path.isfile(getattr(arguments, 'storage_file', '')):
    argument_parser.print_help()
    print ''
    argument_parser.print_usage()
    print ''
    logging.error(u'No storage file supplied.')
    sys.exit(1)

  if arguments.subcommand == 'cluster':
    clustering_engine = ClusteringEngine(
        arguments.storage_file, int(arguments.cluster_threshold, 10),
        int(arguments.cluster_closeness, 10))
    clustering_engine.Run()

  elif arguments.subcommand == 'group':
    grouping_engine = GroupingEngine(
        arguments.storage_file, arguments.quiet)
    grouping_engine.Run()

  elif arguments.subcommand == 'tag':
    if not getattr(arguments, 'tag_filename', ''):
      argument_parser.print_help()
      print ''
      argument_parser.print_usage()
      print ''
      logging.error(u'No tag file supplied.')
      sys.exit(1)

    if not os.path.isfile(arguments.tag_filename):
      logging.error(u'Tag file [{0:s}] does not exist.'.format(
          arguments.tag_filename))
      sys.exit(1)

    tagging_engine = TaggingEngine(
        arguments.storage_file, arguments.tag_filename, arguments.quiet)
    tagging_engine.Run()

if __name__ == '__main__':
  Main()
