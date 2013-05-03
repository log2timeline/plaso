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
"""The storage mechanism for Plaso.

The storage mechanism can be described as a collection of storage files
that are stored together in a single ZIP compressed container.

Each storage file contains several serialized events (as protobufs)
that are fully sorted. However, since the storage container can contain
more than one storage file the overall storage is not fully sorted.

The basic structure of a single storage file in Plaso is:
  plaso_meta.<seq_num>
  plaso_proto.<seq_num>
  plaso_index.<seq_num>

Where the meta file is a simple text file using YAML for variable
definition, example:
  variable: value
  a_list: [value, value, value]

This can be used to filter out which proto files should be included
in processing.

The index file contains an index to all the entries stored within
the protobuf file, so that it can be easily seeked. The layout is:

+-----+-----+-...+
| int | int | ...|
+-----+-----+-...+

Where int is an unsigned integer '<I' that represents the byte offset
into the .proto file where the beginning of the size variable lies.

This can be used to seek the proto file directly to read a particular
entry within the proto file.

Otherwise the structure of a proto file is:
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
import heapq
import logging
import struct
import sys
import zipfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import limit
from plaso.lib import pfilter
from plaso.lib import preprocess
from plaso.lib import queue
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2

from google.protobuf import message
import yaml

__pychecker__ = 'no-abstract'


class PlasoStorage(object):
  """Abstract the storage reading and writing."""

  # Set the buffer size to 196MiB
  MAX_BUFFER_SIZE = 1024 * 1024 * 196

  # Set the version of this storage mechanism.
  STORAGE_VERSION = 1

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
        __pychecker__ = 'no-abstract'
        pre_obj.counter = collections.Counter()
        if hasattr(pre_obj, 'collection_information'):
          pre_obj.collection_information['cmd_line'] = u' '.join(sys.argv)

      # Start up a counter for modules in buffer.
      self._count_evt_long = collections.Counter()
      self._count_evt_short = collections.Counter()
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

      __pychecker__ = 'unusednames=_'
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

  def SetStoreLimit(self, my_filter=None):
    """Set a limit to the stores used for returning data."""
    if not hasattr(self, '_store_range'):
      self._store_range = []

    # Retrieve set first and last timestamps.
    self._GetTimeBounds()

    for number in self.GetProtoNumbers():
      # TODO: Read more criteria from here.
      first, last = self.ReadMeta(number).get('range', (0, limit.MAX_INT64))
      if last < first:
        logging.error('last: %d first: %d container: %d (last < first)',
                      last, first, number)

      if first <= self._bound_last and self._bound_first <= last:
        self._store_range.append(number)
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
      number_range = getattr(self, '_store_range', list(self.GetProtoNumbers()))
      for store_number in number_range:
        if proto_out:
          event_object = self.GetProtoEntry(store_number)
        else:
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

  def AddEntry(self, event_str):
    """Add an entry into the buffer.

    Args:
      event_str: A serialized EventObject to append to the buffer.

    Raises:
      IOError: When trying to write to a closed storage file.
    """
    if not self._file_open:
      raise IOError('Trying to add an entry to a closed storage file.')

    evt = event.EventObject()
    evt.FromProtoString(event_str)

    if evt.timestamp > self._buffer_last_timestamp:
      self._buffer_last_timestamp = evt.timestamp

    if evt.timestamp < self._buffer_first_timestamp and evt.timestamp > 0:
      self._buffer_first_timestamp = evt.timestamp

    # Add values to counters.
    if self._pre_obj:
      self._pre_obj.counter['total'] += 1
      self._pre_obj.counter[evt.attributes.get('parser', 'N/A')] += 1

    # Add to temporary counter.
    self._count_evt_long[evt.source_long] += 1
    self._count_evt_short[evt.source_short] += 1
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

    meta_fh = 'plaso_meta.%06d' % self._filenumber
    proto_fh = 'plaso_proto.%06d' % self._filenumber
    index_fh = 'plaso_index.%06d' % self._filenumber

    yaml_dict = {'range': (self._buffer_first_timestamp,
                           self._buffer_last_timestamp),
                 'version': self.STORAGE_VERSION,
                 'source_short': list(self._count_evt_short.viewkeys()),
                 'source_long': list(self._count_evt_long.viewkeys()),
                 'parsers': list(self._count_parser.viewkeys()),
                 'count': len(self._buffer),
                 'source_count': self._count_evt_long.most_common()}
    self._count_evt_long = collections.Counter()
    self._count_evt_short = collections.Counter()
    self._count_parser = collections.Counter()
    self.zipfile.writestr(meta_fh, yaml.safe_dump(yaml_dict))

    ofs = 0
    proto_str = []
    index_str = []
    __pychecker__ = 'unusednames=_'
    for _ in range(len(self._buffer)):
      _, entry = heapq.heappop(self._buffer)
      # TODO: Instead of appending to an array
      # which is not optimal (loads up the entire max file
      # size into memory) Zipfile should be extended to
      # allow appending to files (implement lock).
      index_str.append(struct.pack('<I', ofs))
      packed = struct.pack('<I', len(entry)) + entry
      ofs += len(packed)
      proto_str.append(packed)

    self.zipfile.writestr(index_fh, ''.join(index_str))
    self.zipfile.writestr(proto_fh, ''.join(proto_str))

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
      size += len(packed)
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
      tag_str = tag.ToProtoString()
      packed = struct.pack('<I', len(tag_str)) + tag_str
      ofs = struct.pack('<I', size)
      sn = struct.pack('<I', tag.store_number)
      si = struct.pack('<I', tag.store_index)
      tag_index.append('%s%s%s' % (ofs, sn, si))
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
        group_entry = self._GetGroupEntry(fh)
        while group_entry:
          yield group_entry
          group_entry = self._GetGroupEntry(fh)

  def _GetGroupEntry(self, fh):
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

  def GetTag(self, store_number, store_index):
    """Return a EventTagging proto if it exists from a store number and index.

    Args:
      store_number: The EventObject store number.
      store_index: The EventObject store index.

    Returns:
      An EventTagging protobuf, if one exists.
    """
    for name in self.zipfile.namelist():
      if 'plaso_tag_index.' in name:
        fh = self.zipfile.open(name, 'r')
        number = int(name.split('.')[-1])

        tag_ofs = self._GetTagFromIndex(fh, store_number, store_index)
        if tag_ofs:
          tag_fh = self.zipfile.open('plaso_tagging.%06d' % number, 'r')
          __pychecker__ = 'unusednames=_'
          _  = tag_fh.read(tag_ofs)
          tag = self._GetTagEntry(tag_fh)

          if tag:
            return tag

  def _GetTagFromIndex(self, fh, store_number, store_index):
    """Return an offset into a tag store for a given store number and index.

    Search through an index file that maintains information about where
    tag information lies in the plaso_tagging. files that store the actual
    EventTagging protobuf.

    Args:
      fh: The filehandle to the tag index file.
      store_number: The store number of the EventObject we are looking for.
      store_index: The index into that store.

    Returns:
      An offset into where the EventTagging protobuf is stored.
    """
    while 1:
      raw = fh.read(12)
      if not raw:
        break
      ofs, sn, si = struct.unpack('<III', raw)
      if store_number != sn:
        continue

      if store_index == si:
        return ofs

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

    size = struct.unpack('<I', unpacked)[0]

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

  __pychecker__ = 'unusednames=unused_type,unused_value,unused_traceback'
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
    self.output = output_file
    self.buffer_size = buffer_size
    self._pre_obj = pre

  def Run(self):
    """Start the storage."""
    with PlasoStorage(
        self.output, buffer_size=self.buffer_size,
        pre_obj=self._pre_obj) as storage_buffer:
      for item in self._queue.PopItems():
        storage_buffer.AddEntry(item)

  def AddEvent(self, item):
    """Add an event to the storage."""
    self._queue.Queue(item)

  def Close(self):
    """Close the queue, indicating to the storage to flush and close."""
    self._queue.Close()
