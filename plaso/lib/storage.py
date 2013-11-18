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
"""The storage mechanism for Plaso.

The storage mechanism can be described as a collection of storage files
that are stored together in a single ZIP compressed container.

The storage file is essentially split up in two categories:
   +  A store file (further described below).
   +  Other files, these contain grouping information, tag, collection
      information or other metadata describing the content of the store files.

The store itself is a collection of four files:
  plaso_meta.<store_number>
  plaso_proto.<store_number>
  plaso_index.<store_number>
  plaso_timestamps.<store_number>

The plaso_proto file within each store contains several serialized EventObjects
or events that are serialized (as a protobuf). All of the EventObjects within
the plaso_proto file are fully sorted based on time however since the storage
container can contain more than one store the overall storage is not fully
sorted.

The other files that make up the store are:

  + plaso_meta

Simple text file using YAML for storing metadata information about the store.
definition, example:
  variable: value
  a_list: [value, value, value]

This can be used to filter out which proto files should be included
in processing.

  + plaso_index

The index file contains an index to all the entries stored within
the protobuf file, so that it can be easily seeked. The layout is:

+-----+-----+-...+
| int | int | ...|
+-----+-----+-...+

Where int is an unsigned integer '<I' that represents the byte offset
into the .proto file where the beginning of the size variable lies.

This can be used to seek the proto file directly to read a particular
entry within the proto file.

  + plaso_timestamps

This is a simple file that contains all the timestamp values of the entries
within the proto file. Each entry is a a long int ('<q') that contains the value
of the EventObject of that timestamps index into the file.

The structure is:
+-----------+-----------+-...-+
| timestamp | timestamp | ... |
+-----------+-----------+-...-+

This is used for time based filtering, where if the 15th entry in this file is
the first entry that is larger than the lower bound, then the index file is used
to seek to the 15th entry inside the proto file.

  + plaso_proto

The structure of a proto file is:
+------+---------------------------------+------+------...+
| size |  protobuf (plaso_storage_proto) | size | proto...|
+------+---------------------------------+------+------...+

For further details about the storage design see:
  http://plaso.kiddaland.net/developer/libraries/storage
"""
# TODO: Go through the storage library to see if it can be split in two, one
# part which will define the storage itself, and can be relatively independent.
# Independent enough to be split into separate project to ease integration by
# other tools. This file will then contain the queueing mechanism and other
# plaso specific mechanism, making it easier to import the storage library.
import collections
import construct
import heapq
import logging
import struct
import sys
import time
import zipfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import limit
from plaso.lib import pfilter
from plaso.lib import output
from plaso.lib import preprocess
from plaso.lib import queue
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2

from google.protobuf import message
import yaml


class PlasoStorage(object):
  """Abstract the storage reading and writing."""

  # Set the buffer size to 196MiB
  MAX_BUFFER_SIZE = 1024 * 1024 * 196

  # Set the version of this storage mechanism.
  STORAGE_VERSION = 1

  # Define structs.
  TAG_STORE_STRUCT = construct.Struct(
      'tag_store', construct.ULInt32('store_number'),
      construct.ULInt32('store_index'))

  TAG_UUID_STRUCT = construct.Struct(
      'tag_uuid', construct.PascalString('event_uuid'))

  TAG_INDEX_STRUCT = construct.Struct(
      'tag_index', construct.Byte('type'), construct.ULInt32('offset'),
      construct.IfThenElse(
          'tag', lambda ctx: ctx['type'] == 1, TAG_STORE_STRUCT,
          TAG_UUID_STRUCT))

  INTEGER = construct.ULInt32('integer')

  source_short_map = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      'SourceShort'].values:
    source_short_map[value.name] = value.number

  def __init__(self, output_file, buffer_size=0, read_only=False,
               pre_obj=None):
    """Constructor for PlasoStorage.

    Args:
      output_file: The name of the output file.
      buffer_size: The estimated size of a protobuf file.
      read_only: Indicate we are just opening up ZIP file for reading.
      pre_obj: A preprocessing object that gets stored inside the storage
      if defined.

    Raises:
      IOError: if we open up the file in read only mode and the file does
      not exist.
    """
    compression = zipfile.ZIP_DEFLATED

    self._filenumber = 1
    self._buffer = []
    self._buffer_size = 0
    self.protofiles = {}
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0
    self._max_buffer_size = buffer_size or self.MAX_BUFFER_SIZE
    self._write_counter = 0
    self._pre_obj = pre_obj
    self._read_only = read_only

    if read_only:
      mode = 'r'
    else:
      mode = 'a'

    try:
      self.zipfile = zipfile.ZipFile(output_file, mode, compression)
    except zipfile.BadZipfile as e:
      raise IOError('Not a ZIP file, cannot read. Error message: %s', e)
    self._file_open = True

    if not read_only:
      logging.debug('Writing to file. Buffer size used: %s',
                    self._max_buffer_size)

      if pre_obj:
        pre_obj.counter = collections.Counter()
        if hasattr(pre_obj, 'collection_information'):
          cmd_line = ' '.join(sys.argv)
          encoding = getattr(pre_obj, 'preferred_encoding', None)
          if encoding:
            try:
              cmd_line = cmd_line.decode(encoding)
            except UnicodeDecodeError:
              pass
          pre_obj.collection_information['cmd_line'] = cmd_line

      # Start up a counter for modules in buffer.
      self._count_data_type = collections.Counter()
      self._count_parser = collections.Counter()

      # Need to get the last number in the list.
      for name in self.zipfile.namelist():
        if 'plaso_meta.' in name:
          _, number = name.split('.')
          if int(number) >= self._filenumber:
            self._filenumber = int(number) + 1

      self._first_filenumber = self._filenumber

  def _StorePreObject(self, pre_obj):
    """Store information gathered during preprocessing to the storage file."""
    strings = []
    try:
      pre_fh = self.zipfile.open('information.dump', 'r')
      while 1:
        read_str = pre_fh.read(1024)
        if not read_str:
          break
        strings.append(read_str)
    except KeyError:
      pass

    # Store information about store range for this particular
    # preprocessing object. This will determine which stores
    # this information is applicaple for.
    stores = list(self.GetProtoNumbers())
    if stores:
      end = stores[-1] + 1
    else:
      end = self._first_filenumber
    pre_obj.store_range = (self._first_filenumber, end)

    serialized = pre_obj.ToProtoString()
    strings.append(struct.pack('<I', len(serialized)) + serialized)
    self.zipfile.writestr('information.dump', ''.join(strings))

  def GetStorageInformation(self):
    """Return gathered preprocessing information from a storage file."""
    information = []
    try:
      pre_fh = self.zipfile.open('information.dump', 'r')
    except KeyError:
      return information

    while 1:
      unpacked = pre_fh.read(4)
      if len(unpacked) != 4:
        break

      size = struct.unpack('<I', unpacked)[0]

      if size > 1024 * 1024 * 40:
        raise errors.WrongProtobufEntry('Protobuf size too large: %d', size)

      serialized = pre_fh.read(size)
      info = preprocess.PlasoPreprocess()
      try:
        info.FromProtoString(serialized)
      except message.DecodeError:
        logging.error('Unable to parse preprocessing object, bailing out.')
        break

      information.append(info)

    stores = list(self.GetProtoNumbers())
    information[-1].stores = {}
    information[-1].stores['Number'] = len(stores)
    for store in stores:
      information[-1].stores['Store %d' % store] = self.ReadMeta(store)

    return information

  def GetNumberOfEvents(self):
    """Retrieves the number of event objects in a storage file."""
    total_events = 0
    if hasattr(self, 'GetStorageInformation'):
      for store_info in self.GetStorageInformation():
        if hasattr(store_info, 'stores'):
          stores = store_info.stores.values()
          for store_file in stores:
            if type(store_file) is dict and 'count' in store_file:
              total_events += store_file['count']
    return total_events

  def _GetEntry(self, number, entry_index=-1):
    """Return a serialized EventObject protobuf read from filehandle.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      number: The proto file number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      A list with two entries: the raw serialized EventObject protobuf and
      an integer indicating the index that protobuf has in the storage file.

    Raises:
      EOFError: When we reach the end of the protobuf file.
      errors.WrongProtobufEntry: If the probotuf size is too large for storage.
    """
    last_index = 0
    if number in self.protofiles:
      fh, last_index = self.protofiles[number]
    else:
      fh = self.zipfile.open('plaso_proto.%06d' % number, 'r')
      self.protofiles[number] = (fh, 0)

    if entry_index > -1:
      index_fh = self.zipfile.open('plaso_index.%06d' % number, 'r')
      ofs = entry_index * 4

      # Since seek is not supported we need to read and ignore the data.
      _ = index_fh.read(ofs)
      size_byte_stream = index_fh.read(4)

      if len(size_byte_stream) != 4:
        logging.error('Unable to read entry number: %d from store %d',
                      entry_index, number)
        return None, None

      ofs = struct.unpack('<I', size_byte_stream)[0]

      # Again, since seek is not supported we need to close the file and reopen
      # it to be able to "fake" seek.
      fh = self.zipfile.open('plaso_proto.%06d' % number, 'r')
      self.protofiles[number] = (fh, entry_index)
      last_index = entry_index
      _ = fh.read(ofs)

    if not last_index and  hasattr(
        self, '_bound_first') and self._bound_first and entry_index == -1:
      # We only get here if the following conditions are met:
      #   1. last_index is not set (so this is the first read from this file).
      #   2. There is a lower bound (so we have a date filter).
      #   3. The lower bound is higher than zero (basically set to a value).
      #   4. We are accessing this function using 'get me the next entry' as an
      #      opposed to the 'get me entry X', where we just want to server entry
      #      X.
      #
      # The purpose: speed seeking into the storage file based on time. Instead
      # of spending precious time reading through the storage file and
      # deserializing protobufs just to compare timestamps we read a much
      # 'cheaper' file, one that only contains timestamps to find the proper
      # entry into the storage file. That way we'll get to the right place in
      # the file and can start reading protobufs from the right location.
      index = 0
      timestamp_filename = 'plaso_timestamps.%06d' % number

      # Recent add-on to the storage file, not certain this file exists.
      if timestamp_filename in self.zipfile.namelist():
        timestamp_fh = self.zipfile.open(timestamp_filename, 'r')
        timestamp_compare = 0
        while timestamp_compare < self._bound_first:
          timestamp_raw = timestamp_fh.read(8)
          if len(timestamp_raw) != 8:
            break
          timestamp_compare = struct.unpack('<q', timestamp_raw)[0]
          index += 1
        return self._GetEntry(number, index)

    # Now we've seeked to the proper location in code.
    unpacked = fh.read(4)

    if len(unpacked) != 4:
      return None, None

    size = struct.unpack('<I', unpacked)[0]

    if size > 1024 * 1024 * 40:
      raise errors.WrongProtobufEntry('Protobuf size too large: %d', size)

    self.protofiles[number] = (fh, last_index + 1)
    return fh.read(size), last_index

  def GetProtoEntry(self, number, entry_index=-1):
    """Return an EventObject protobuf from a filehandle.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      number: The proto file number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      An event protobuf (EventObject) entry read from the file.
    """
    proto = plaso_storage_pb2.EventObject()
    proto_str, last_index = self._GetEntry(number, entry_index)
    if not proto_str:
      return None
    proto.ParseFromString(proto_str)
    proto.store_number = number
    proto.store_index = last_index

    return proto

  def SetStoreLimit(self, my_filter=None):    # pylint:disable-msg=W0613
    """Set a limit to the stores used for returning data."""
    # We are setting the bounds now, remove potential prior bound settings.
    if hasattr(self, '_bound_first'):
      del self._bound_first

    self.store_range = []

    # Retrieve set first and last timestamps.
    self._GetTimeBounds()

    # TODO: Fetch a filter object from the filter query.

    for number in self.GetProtoNumbers():
      # TODO: Read more criteria from here.
      first, last = self.ReadMeta(number).get('range', (0, limit.MAX_INT64))
      if last < first:
        logging.error('last: %d first: %d container: %d (last < first)',
                      last, first, number)

      if first <= self._bound_last and self._bound_first <= last:
        # TODO: Check at least parser and data_type (stored in metadata).
        # Check whether these attributes exist in filter, if so use the filter
        # to determine whether the stores should be included.
        self.store_range.append(number)

      else:
        logging.debug('Store [%d] not used', number)

  def _GetTimeBounds(self):
    """Get the upper and lower time bounds."""
    if hasattr(self, '_bound_first'):
      return

    self._bound_first, self._bound_last = pfilter.TimeRangeCache.GetTimeRange()

  def GetSortedEntry(self, proto_out=False):
    """Return a sorted entry from the storage file.

    Args:
      proto_out: A boolean variable indicating whether or not a protobuf
      or a python object should be returned.

    Returns:
      An EventObject python object, unless proto_out is set then an EventObject
      protobuf is returned back.
    """
    if not hasattr(self, '_bound_first'):
      self._GetTimeBounds()

    if not hasattr(self, '_merge_buffer'):
      self._merge_buffer = []
      number_range = getattr(self, 'store_range', list(self.GetProtoNumbers()))
      for store_number in number_range:
        if proto_out:
          event_object = self.GetProtoEntry(store_number)
          while event_object.timestamp < self._bound_first:
            event_object = self.GetProtoEntry(store_number)
        else:
          event_object = self.GetEntry(store_number)
          while event_object.timestamp < self._bound_first:
            event_object = self.GetEntry(store_number)

        heapq.heappush(
            self._merge_buffer,
            (event_object.timestamp, store_number, event_object))

    if not self._merge_buffer:
      return

    _, store_number, event_read = heapq.heappop(self._merge_buffer)
    if not event_read:
      return

    # Stop as soon as we hit the upper bound.
    if event_read.timestamp > self._bound_last:
      return

    if proto_out:
      new_event_object = self.GetProtoEntry(store_number)
    else:
      new_event_object = self.GetEntry(store_number)

    if new_event_object:
      heapq.heappush(
          self._merge_buffer,
          (new_event_object.timestamp, store_number, new_event_object))

    tag = self.GetTag(
        event_read.store_number, event_read.store_index, event_read.uuid)
    if tag:
      event_read.tag = tag

    return event_read

  def GetEntry(self, number, entry_index=-1):
    """Return an EventObject read from a filehandle.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      number: The proto file number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      An event object (EventObject) entry read from the file.
    """
    event_object = event.EventObject()
    proto_str, last_index = self._GetEntry(number, entry_index)
    if not proto_str:
      return None
    event_object.FromProtoString(proto_str)
    event_object.store_number = number
    event_object.store_index = last_index

    return event_object

  def GetEntries(self, number):
    """A generator to read all plaso_storage protobufs from a filehandle.

    The storage mechanism of Plaso works in the way that it creates potentially
    several files inside the ZIP container. As soon as the number of protobufs
    stored exceed the size of buffer_size they will be flushed to disk as:

          plaso_proto.XXX

    Where XXX is an increasing integer, starting from one. To get all the files
    or the numbers that are available this class implements a method called
    GetProtoNumbers() that returns a list of all available protobuf files within
    the container.

    This method returns a generator that returns all plaso_storage protobufs in
    the named container, as indicated by the number argument. So if this method
    is called as storage_object.GetEntries(1) the generator will return the
    entries found in the file plaso_proto.000001.

    Args:
      number: The protofile number.

    Yields:
      A protobuf object from the protobuf file.
    """
    # TODO: Change this function, don't accespt a store number and implement the
    # MergeSort functionailty of the psort file in here. This will then always
    # return the sorted entries from the storage file, implementing the second
    # stage of the sort/merge algorithm.
    while True:
      try:
        proto = self.GetEntry(number)
        if not proto:
          logging.debug('End of protobuf file plaso_proto.%06d reached.',
                        number)
          break
        yield proto
      except errors.WrongProtobufEntry as e:
        logging.warning(('Problem while parsing a protobuf entry from: '
                         'plaso_proto.%06d <%s>'), number, e)

  def GetProtoNumbers(self):
    """Return all available protobuf numbers."""
    numbers = []
    for name in self.zipfile.namelist():
      if 'plaso_proto' in name:
        _, num = name.split('.')
        numbers.append(int(num))

    for number in sorted(numbers):
      yield number

  def ReadMeta(self, number):
    """Return a dict with the metadata entries.

    Args:
      number: The number of the metadata file (name is plaso_meta_XXX where
              XXX is this number.

    Returns:
      A dict object containing all the variables inside the metadata file.
    """
    meta_file = self.zipfile.open('plaso_meta.%06d' % number, 'r')
    return yaml.safe_load(meta_file)

  def GetBufferSize(self):
    """Return the size of the buffer."""
    return self._buffer_size

  def GetFileNumber(self):
    """Return the current file number of the storage."""
    return self._filenumber

  def AddEntry(self, event_str_or_obj):
    """Add an entry into the buffer.

    Args:
      event_str_or_obj: Either a serialized EventObject or an EventObject
                        object that is appended to the buffer.

    Raises:
      IOError: When trying to write to a closed storage file.
    """
    if not self._file_open:
      raise IOError('Trying to add an entry to a closed storage file.')

    if type(event_str_or_obj) in (str, unicode):
      evt = event.EventObject()
      evt.FromProtoString(event_str_or_obj)
      event_str = event_str_or_obj
    else:
      evt = event_str_or_obj
      event_str = evt.ToProtoString()

    if evt.timestamp > self._buffer_last_timestamp:
      self._buffer_last_timestamp = evt.timestamp

    if evt.timestamp < self._buffer_first_timestamp and evt.timestamp > 0:
      self._buffer_first_timestamp = evt.timestamp

    # Add values to counters.
    if self._pre_obj:
      self._pre_obj.counter['total'] += 1
      self._pre_obj.counter[evt.attributes.get('parser', 'N/A')] += 1

    # Add to temporary counter.
    self._count_data_type[evt.data_type] += 1
    self._count_parser[evt.attributes.get('parser', 'unknown_parser')] += 1

    heapq.heappush(self._buffer, (evt.timestamp, event_str))
    self._buffer_size += len(event_str)
    self._write_counter += 1

    if self._buffer_size > self._max_buffer_size:
      self.FlushBuffer()

  def FlushBuffer(self):
    """Flush a buffer to disk."""

    if not self._buffer_size:
      return

    meta_name = 'plaso_meta.%06d' % self._filenumber
    proto_name = 'plaso_proto.%06d' % self._filenumber
    index_name = 'plaso_index.%06d' % self._filenumber
    timestamp_name = 'plaso_timestamps.%06d' % self._filenumber

    yaml_dict = {'range': (self._buffer_first_timestamp,
                           self._buffer_last_timestamp),
                 'version': self.STORAGE_VERSION,
                 'data_type': list(self._count_data_type.viewkeys()),
                 'parsers': list(self._count_parser.viewkeys()),
                 'count': len(self._buffer),
                 'type_count': self._count_data_type.most_common()}
    self._count_data_type = collections.Counter()
    self._count_parser = collections.Counter()
    self.zipfile.writestr(meta_name, yaml.safe_dump(yaml_dict))

    ofs = 0
    proto_str = []
    index_str = []
    timestamp_str = []
    for _ in range(len(self._buffer)):
      timestamp, entry = heapq.heappop(self._buffer)
      # TODO: Instead of appending to an array
      # which is not optimal (loads up the entire max file
      # size into memory) Zipfile should be extended to
      # allow appending to files (implement lock).
      index_str.append(struct.pack('<I', ofs))
      timestamp_str.append(struct.pack('<q', timestamp))
      packed = struct.pack('<I', len(entry)) + entry
      ofs += len(packed)
      proto_str.append(packed)

    self.zipfile.writestr(index_name, ''.join(index_str))
    self.zipfile.writestr(proto_name, ''.join(proto_str))
    self.zipfile.writestr(timestamp_name, ''.join(timestamp_str))

    self._filenumber += 1
    self._buffer_size = 0
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0

  def HasTagging(self):
    """Return a bool indicating whether or not a Tag file is stored."""
    for name in self.zipfile.namelist():
      if 'plaso_tagging.' in name:
        return True
    return False

  def HasGrouping(self):
    """Return a bool indicating whether or not a Group file is stored."""
    for name in self.zipfile.namelist():
      if 'plaso_grouping.' in name:
        return True
    return False

  def StoreGrouping(self, rows):
    """Store group information into the storage file.

    An EventGroup protobuf stores information about several
    EventObjects that belong to the same behavior or action. It can then
    be used to group similar events together to create a super event, or
    a higher level event.

    This function is used to store that information inside the storage
    file so it can be read later.

    The object that is passed in needs to have an iterator implemented
    and has to implement the following attributes (optional names within
    bracket):
      name - The name of the grouped event.
      [description] - More detailed description of the event.
      [category] - If this group of events falls into a specific category.
      [color] - To highlight this particular group with a HTML color tag.
      [first_timestamp] - The first timestamp if applicaple of the group.
      [last_timestamp] - The last timestamp if applicaple of the group.
      events - A list of tuples (store_number and store_index of the
      EventObject protobuf that belongs to this group of events).

    Args:
      rows: An object that contains the necessary fields to contruct
      an EventGroup. Has to be a generator object or an object that implements
      an iterator.
    """
    group_number = 1
    if self.HasGrouping():
      for name in self.zipfile.namelist():
        if 'plaso_grouping.' in name:
          _, number = name.split('.')
          if int(number) >= group_number:
            group_number = int(number) + 1

    group_packed = []
    size = 0
    for row in rows:
      group = plaso_storage_pb2.EventGroup()
      group.name = row.name
      if hasattr(row, 'description'):
        group.description = utils.GetUnicodeString(row.description)
      if hasattr(row, 'category'):
        group.category = utils.GetUnicodeString(row.category)
      if hasattr(row, 'color'):
        group.color = utils.GetUnicodeString(row.color)

      for number, index in row.events:
        evt = group.events.add()
        evt.store_number = int(number)
        evt.store_index = int(index)

      if hasattr(row, 'first_timestamp'):
        group.first_timestamp = int(row.first_timestamp)
      if hasattr(row, 'last_timestamp'):
        group.last_timestamp = int(row.last_timestamp)

      group_str = group.SerializeToString()
      packed = struct.pack('<I', len(group_str)) + group_str
      # TODO: Size is defined, should be used to determine if we've filled
      # our buffer size of group information. Check that and write a new
      # group store file in that case.
      size += len(packed)
      if size > self._max_buffer_size:
        logging.warning(u'Grouping has outgrown buffer size.')
      group_packed.append(packed)

    self.zipfile.writestr('plaso_grouping.%06d' % group_number,
                          ''.join(group_packed))

  def StoreTagging(self, tags):
    """Store tag information into the storage file.

    Each EventObject can be tagged either manually or automatically
    to make analysis simpler, by providing more context to certain
    events or to highlight events for later viewing.

    The object passed in needs to be a list (or otherwise an iterator)
    that contains EventTag objects (event.EventTag).

    Args:
      tags: A list or an object providing an iterator that contains
      EventTag objects.
    """
    if not self._pre_obj:
      self._pre_obj = preprocess.PlasoPreprocess()

    if not hasattr(self._pre_obj, 'collection_information'):
      self._pre_obj.collection_information = {}

    self._pre_obj.collection_information['Action'] = 'Adding tags to storage.'
    self._pre_obj.collection_information['time_of_run'] = time.time()
    self._pre_obj.counter = collections.Counter()

    tag_number = 1
    if self.HasTagging():
      for name in self.zipfile.namelist():
        if 'plaso_tagging.' in name:
          _, number = name.split('.')
          if int(number) >= tag_number:
            tag_number = int(number) + 1

    tag_packed = []
    tag_index = []
    size = 0
    for tag in tags:
      self._pre_obj.counter['Total'] += 1
      if hasattr(tag, 'tags'):
        for tag_entry in tag.tags:
          self._pre_obj.counter[tag_entry] += 1
      tag_str = tag.ToProtoString()
      packed = struct.pack('<I', len(tag_str)) + tag_str
      ofs = struct.pack('<I', size)
      if getattr(tag, 'store_number', 0):
        struct_string = construct.Byte(
            'type').build(1) + ofs + self.TAG_STORE_STRUCT.build(tag)
      else:
        struct_string = construct.Byte(
            'type').build(2) + ofs + self.TAG_UUID_STRUCT.build(tag)

      tag_index.append(struct_string)
      size += len(packed)
      tag_packed.append(packed)

    self.zipfile.writestr('plaso_tag_index.%06d' % tag_number,
                          ''.join(tag_index))
    self.zipfile.writestr('plaso_tagging.%06d' % tag_number,
                          ''.join(tag_packed))

  def GetGrouping(self):
    """Return a generator that reads all grouping information from storage."""
    if not self.HasGrouping():
      return

    for name in self.zipfile.namelist():
      if 'plaso_grouping.' in name:
        fh = self.zipfile.open(name, 'r')
        group_entry = GetEventGroupProto(fh)
        while group_entry:
          yield group_entry
          group_entry = GetEventGroupProto(fh)

  def GetTag(self, store_number, store_index, uuid):
    """Return a EventTagging proto if it exists from a store number and index.

    Args:
      store_number: The EventObject store number.
      store_index: The EventObject store index.
      uuid: The EventObject UUID value.

    Returns:
      An EventTagging protobuf, if one exists.
    """
    if not hasattr(self, '_tag_memory'):
      self._ReadTagInformationIntoMemory()

    key_index = '{}:{}'.format(store_number, store_index)

    if key_index not in self._tag_memory:
      key_index = uuid

    if key_index not in self._tag_memory:
      return

    tag_store, tag_offset = self._tag_memory.get(key_index)

    tag_fh = self.zipfile.open('plaso_tagging.%06d' % tag_store , 'r')
    _  = tag_fh.read(tag_offset)
    return self._GetTagEntry(tag_fh)

  def _ReadTagInformationIntoMemory(self):
    """Build a dict that maintains tag offset information for quick reading."""
    self._tag_memory = {}

    for name in self.zipfile.namelist():
      if not 'plaso_tag_index.' in name:
        continue
      fh = self.zipfile.open(name, 'r')
      _, _, number_str = name.rpartition('.')
      number = int(number_str)
      while 1:
        try:
          tag_index = self.TAG_INDEX_STRUCT.parse_stream(fh)
        except (construct.FieldError, AttributeError):
          break

        tag_type = tag_index.get('type', 0)
        tag_entry = tag_index.get('tag', {})
        if tag_type == 1:
          read_key = '{}:{}'.format(
              tag_entry.get('store_number', 0),
              tag_entry.get('store_index', 0))
        elif tag_type == 2:
          read_key = tag_entry.get('event_uuid', '0')
        else:
          logging.warning('Unknown tag type: {}'.format(tag_type))
          break

        offset = tag_index.get('offset')
        self._tag_memory[read_key] = (number, offset)

  def GetTagging(self):
    """Return a generator that reads all tagging information from storage.

    This function reads all tagging files inside the storage and returns
    back the EventTagging protobuf, and only that protobuf.

    To get the full EventObject with tags attached it is possible to use
    the GetTaggedEvent and pass the EventTagging protobuf to it.

    Yields:
      All EventTag objects stored inside the storage container.
    """
    if not self.HasTagging():
      return

    for name in self.zipfile.namelist():
      if 'plaso_tagging.' in name:
        fh = self.zipfile.open(name, 'r')

        tag_entry = self._GetTagEntry(fh)
        while tag_entry:
          yield tag_entry
          tag_entry = self._GetTagEntry(fh)

  def GetEventsFromGroup(self, group_proto):
    """Return a generator with all EventObjects from a group."""
    for group_event in group_proto.events:
      yield self.GetEntry(group_event.store_number, group_event.store_index)

  def GetTaggedEvent(self, tag_event):
    """Read in an EventTag object from a tag and return an EventObject.

    This function uses the information inside the EventTag object
    to open the EventObject that was tagged and returns it, with the
    tag information attached to it.

    Args:
      tag_event: An EventTag object.

    Returns:
      An EventObject with the EventTag object attached.
    """
    evt = self.GetEntry(tag_event.store_number, tag_event.store_index)
    if not evt:
      return None

    evt.tag = tag_event

    return evt

  def _GetTagEntry(self, fh):
    """Read a single EventTag from a tag store file."""
    unpacked = fh.read(4)
    if len(unpacked) != 4:
      return None

    size = self.INTEGER.parse(unpacked)

    if size > 1024 * 1024 * 40:
      raise errors.WrongProtobufEntry('Protobuf size too large: %d', size)

    proto_serialized = fh.read(size)
    event_tag = event.EventTag()
    event_tag.FromProtoString(proto_serialized)
    return event_tag

  def CloseStorage(self):
    """Closes the storage, flush the last buffer and closes the ZIP file."""
    if self._file_open:
      if self._pre_obj:
        self._StorePreObject(self._pre_obj)
      self.FlushBuffer()
      self.zipfile.close()
      self._file_open = False
      if not self._read_only:
        logging.info(('[Storage] Closing the storage, nr. of events processed:'
                      ' %d'), self._write_counter)

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.CloseStorage()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


class SimpleStorageDumper(object):
  """Watch a queue with EventObjects and process them for storage."""

  def __init__(self, output_file, buffer_size=0, pre=None):
    """Constructor for the storage.

    Args:
      output_file: The path to the output file.
      buffer_size: The estimated size of a protobuf file.
      pre: A pre-processing object.
    """
    self._queue = queue.MultiThreadedQueue()
    self.output_file = output_file
    self.buffer_size = buffer_size
    self._pre_obj = pre

  def Run(self):
    """Start the storage."""
    with PlasoStorage(
        self.output_file, buffer_size=self.buffer_size,
        pre_obj=self._pre_obj) as storage_buffer:
      for item in self._queue.PopItems():
        storage_buffer.AddEntry(item)

  def AddEvent(self, item):
    """Add an event to the storage."""
    self._queue.Queue(item)

  def Close(self):
    """Close the queue, indicating to the storage to flush and close."""
    self._queue.Close()


class BypassStorageDumper(object):
  """Watch a queue with EventObjects and send them directly to output."""

  def __init__(self, output_file, output_module_string='lst2csv', pre=None):
    """Initialize an object that bypasses the storage library."""
    self.output_file = output_file
    output_class = output.GetOutputFormatter(output_module_string)
    self._queue = queue.MultiThreadedQueue()

    self._pre_obj = pre
    self._pre_obj.store_range = (1, 1)

    if not output_class:
      output_class = output.GetOutputFormatter('Lst2csv')

    self.output_module = output_class(self, output_file, config=self._pre_obj)
    self.output_module.Start()

  def Run(self):
    """Run the storage until no event comes in."""
    for item in self._queue.PopItems():
      self.ProcessEntry(item)

  def AddEvent(self, item):
    """Add an event to the output."""
    self._queue.Queue(item)

  def ProcessEntry(self, item):
    """Process an event and send it to an output module."""
    event_object = event.EventObject()
    event_object.FromProtoString(item)
    event_object.store_number = 1
    event_object.store_index = -1

    self.output_module.WriteEvent(event_object)

  def GetStorageInformation(self):
    """Return information about the storage object (used by output modules)."""
    ret = []
    ret.append(self._pre_obj)

    return ret

  def Close(self):
    """Close the storage, in this case indicate the output that we are done."""
    self._queue.Close()
    self.output_module.End()


def GetEventGroupProto(fh):
  """Return a single group entry from a filehandle."""
  unpacked = fh.read(4)
  if len(unpacked) != 4:
    return None

  size = struct.unpack('<I', unpacked)[0]

  if size > 1024 * 1024 * 40:
    raise errors.WrongProtobufEntry('Protobuf size too large: %d', size)

  proto_serialized = fh.read(size)
  proto = plaso_storage_pb2.EventGroup()

  proto.ParseFromString(proto_serialized)
  return proto

